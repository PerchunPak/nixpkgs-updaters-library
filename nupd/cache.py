import collections.abc as c
import functools
import inspect
import json
import shelve
import typing as t
from collections import OrderedDict
from pathlib import Path

import platformdirs


def get_cache_dir() -> Path:
    location = Path(platformdirs.user_cache_dir("nupd", "PerchunPak"))
    location.mkdir(parents=True, exist_ok=True)
    return location


def _recursive_to_list[T](inp: c.Iterable[T]) -> list[T]:
    result: list[T] = []

    for v in list(inp):
        if isinstance(v, c.Iterable) and not isinstance(v, str):
            result.append(_recursive_to_list(v))
        else:
            result.append(v)

    return result


def _get_key_for_caching[R](
    signature: inspect.Signature,
    args: c.Sequence[R],
    kwargs: c.Mapping[str, R],
    *,
    function_name: str,
) -> dict[str, list[R] | R]:
    pos_args: list[str] = []
    var_pos_arg: str | None = None
    for name, arg in signature.parameters.items():
        if arg.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            pos_args.append(name)
        elif arg.kind is inspect.Parameter.VAR_POSITIONAL:
            var_pos_arg = name

    if len(args) > len(pos_args) and var_pos_arg is None:
        raise RuntimeError("You provided wrong amount of positional arguments!")

    result: dict[str, list[R] | R] = t.cast(
        dict[str, list[R] | R], kwargs
    ).copy()

    for i in range(len(args)):
        try:
            name = pos_args[i]
        except IndexError:
            assert var_pos_arg is not None
            _ = result.setdefault(var_pos_arg, [])
            t.cast(list[R], result[var_pos_arg]).append(args[i])
        else:
            if name in kwargs:
                raise TypeError(
                    f"{function_name}() got multiple values for argument '{name}'"
                )
            result[name] = args[i]

    return result


type CACHE_STORAGE[R] = dict[
    tuple[tuple[t.Any, ...], frozenset[tuple[c.Hashable, c.Hashable]]], R
]


def _to_ordered_dict[K, V](kwargs: dict[K, V]) -> OrderedDict[K, V]:
    sorted_dict: OrderedDict[K, V] = OrderedDict()
    for key, value in kwargs.items():
        if isinstance(value, dict):
            sorted_dict[key] = _to_ordered_dict(value)
        else:
            sorted_dict[key] = value
    return sorted_dict


@t.overload
def cache_result[F: c.Callable[..., t.Any]](func: F, /) -> F: ...


@t.overload
def cache_result[F: c.Callable[..., t.Any]](
    *, save_on_disk: t.Literal[False] = False
) -> c.Callable[[F], F]: ...


@t.overload
def cache_result[F: c.Callable[..., t.Any]](
    *, save_on_disk: t.Literal[True], id: str
) -> c.Callable[[F], F]: ...


def cache_result[**P, R](
    func: c.Callable[P, R] | None = None,
    /,
    *,
    save_on_disk: bool = False,
    id: str | None = None,  # noqa: A002
) -> c.Callable[P, R] | c.Callable[[c.Callable[P, R]], c.Callable[P, R]]:
    if func is not None:
        return functools.cache(func)  # pyright: ignore[reportReturnType]

    if save_on_disk is False:
        return functools.cache  # pyright: ignore[reportReturnType]

    assert id is not None
    cache_file = get_cache_dir() / (id + ".shelve")
    data: shelve.Shelf[R] = shelve.open(cache_file)  # noqa: SIM115,S301

    def decorator(func: c.Callable[P, R]) -> c.Callable[P, R]:
        func._data = (  # pyright: ignore[reportFunctionMemberAccess]
            data  # for tests
        )
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = json.dumps(
                _get_key_for_caching(
                    signature, args, kwargs, function_name=func.__name__
                )
            )
            if (cached := data.get(key)) is not None:
                return cached

            result = func(*args, **kwargs)
            data[key] = result
            return result

        return wrapper

    return decorator
