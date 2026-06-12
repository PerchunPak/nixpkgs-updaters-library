from __future__ import annotations

import asyncio
import copy
import dataclasses
import typing as t
from os import PathLike
from pathlib import Path

import joblib
import platformdirs
import pydantic_core
import rich.progress
from frozendict import frozendict
from pydantic import BaseModel
from rich.console import Console

from nupd.exc import GitError
from nupd.executables import Executable

if t.TYPE_CHECKING:
    import pydantic
    from joblib.memory import MemorizedFunc

    from nupd.models import ImplClasses

console = Console(stderr=True)
memory = joblib.Memory(
    platformdirs.user_cache_path("nupd", "PerchunPak") / "cache", verbose=0
)

NIXPKGS_PLACEHOLDER = Path(f"/nixpkgs_{id(object())}")
"""Dummy path that is used to specify nixpkgs root in default input/output file location."""  # noqa: E501


class _PydanticFrozenDictAnnotation[K, V]:
    """https://github.com/pydantic/pydantic/discussions/8721#discussioncomment-9753166."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: t.Any, handler: pydantic.GetCoreSchemaHandler
    ) -> pydantic_core.core_schema.CoreSchema:
        def validate_from_dict(
            d: dict[K, V] | frozendict[K, V],
        ) -> frozendict[K, V]:
            return frozendict(d)

        frozendict_schema = pydantic_core.core_schema.chain_schema(
            [
                handler.generate_schema(dict[*t.get_args(source_type)]),  # pyright: ignore[reportInvalidTypeArguments]
                pydantic_core.core_schema.no_info_plain_validator_function(
                    validate_from_dict
                ),
                pydantic_core.core_schema.is_instance_schema(frozendict),
            ]
        )
        return pydantic_core.core_schema.json_or_python_schema(
            json_schema=frozendict_schema,
            python_schema=frozendict_schema,
            serialization=pydantic_core.core_schema.plain_serializer_function_ser_schema(
                dict
            ),
        )


type FrozenDict[K, V] = t.Annotated[
    frozendict[K, V], _PydanticFrozenDictAnnotation
]


def replace[T](obj: T, **changes: t.Any) -> T:
    """Analogue for `copy.replace` that works with dataclasses and pydantic."""
    result = copy.copy(obj)

    if dataclasses.is_dataclass(obj):
        for field_name, value in changes.items():
            if field_name not in {f.name for f in dataclasses.fields(obj)}:
                raise TypeError(
                    f"'{type(obj).__name__}' has no field named '{field_name}'"
                )
            object.__setattr__(result, field_name, value)

        return result

    if isinstance(obj, BaseModel):
        updated = obj.model_dump(mode="json")
        updated.update(changes)
        return type(obj)(**updated)

    raise TypeError(
        "replace() can be called on dataclass or pydantic instances"
    )


def cleanup_raw_string(arg: str | t.Any) -> str:
    """Clean up some common unnecessary symbols like leading/trailing spaces.

    Basically this tries to make a string, that is compatible with
    `meta.description` in
    https://github.com/NixOS/nixpkgs/tree/master/pkgs#meta-attributes.
    """
    # for scripting easibility, if it is not a string, just return it.
    # this allows us to use this function as a pydantic "before" validator
    # on e.g. optional values
    if not isinstance(arg, str):
        return arg
    result = arg.strip().strip(".")
    # capitalize first letter
    result = result[:1].upper() + result[1:]
    result = result.removeprefix("The ").removeprefix("A ")

    if result == arg:
        return result
    return cleanup_raw_string(result)


def restore_docstring_from_memoized_function[R, **P](
    func: MemorizedFunc[P, R],
) -> MemorizedFunc[P, R]:
    func.__doc__ = func.func.__doc__  # pyright: ignore[reportAttributeAccessIssue]
    return func


def cache_validate_by_revision(args: dict[str, t.Any]) -> bool:
    """Never delete cache if ``revision`` argument was provided."""
    if args["input_args"].get("revision"):
        return True
    return joblib.expires_after(hours=1)(args)


def register_implementation_classes(  # pragma: no cover
    impl: ImplClasses,
) -> None:
    register_implementation_classes.impl = impl  # pyright: ignore[reportFunctionMemberAccess]


def get_formatted_progress_bar() -> tuple[
    str | rich.progress.ProgressColumn, ...
]:
    return (
        "[progress.description]{task.description}",
        rich.progress.MofNCompleteColumn(),
        rich.progress.BarColumn(),
        "[",
        rich.progress.TimeElapsedColumn(),
        rich.progress.TimeRemainingColumn(),
        "]",
    )


async def git_commit(message: str, cwd: PathLike[str] | None = None) -> None:
    process = await asyncio.create_subprocess_exec(
        Executable.GIT,
        "commit",
        "-a",
        "--message",
        message,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise GitError(
            f"git returned exit code {process.returncode}"
            + f"\n{stdout=}\n{stderr=}"
        )
    if stderr.decode() != "":
        raise GitError(f"git wrote something to stderr!\n{stdout=}\n{stderr=}")
