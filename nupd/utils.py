from __future__ import annotations

import asyncio
import copy
import dataclasses
import functools
import typing as t
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import joblib  # pyright: ignore[reportMissingTypeStubs] # stubs are not packaged in nixpkgs
import platformdirs
import pydantic_core
from frozendict import frozendict
from pydantic import BaseModel, BeforeValidator

if t.TYPE_CHECKING:
    import collections.abc as c

    import pydantic

memory = joblib.Memory(
    platformdirs.user_cache_path("nupd", "PerchunPak") / "cache", verbose=0
)


def async_to_sync[**P, R](  # pragma: no cover
    f: c.Callable[P, c.Coroutine[t.Any, t.Any, R]],
) -> c.Callable[P, R]:
    @wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> R:
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def sync_to_async[**P, R](  # pragma: no cover
    f: c.Callable[P, R],
) -> c.Callable[P, c.Awaitable[R]]:
    executor = ThreadPoolExecutor(1)

    @wraps(f)
    async def wrapper(*args: t.Any, **kwargs: t.Any) -> R:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor, functools.partial(f, *args, **kwargs)
        )

    return wrapper


def chunks[T](lst: c.Sequence[T], n: int) -> c.Iterable[c.Sequence[T]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


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
    """Analogue for `copy.replace` that works with 3.12 and dataclasses and pydantic."""
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


def nullify(arg: str | t.Any) -> str | None:
    """`arg if arg else None`.

    This helps to transform something like an empty string to a None.
    """
    return arg if arg else None


def cleanup_raw_string(arg: str | t.Any) -> str:
    """Clean up some common unnecessary symbols like leading/trailing spaces.

    Basically this tries to make a string, that is compatible with `meta.description`
    in https://github.com/NixOS/nixpkgs/tree/master/pkgs#meta-attributes.
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


type CleanedUpString = t.Annotated[str, BeforeValidator(cleanup_raw_string)]
