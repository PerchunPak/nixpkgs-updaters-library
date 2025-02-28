from __future__ import annotations

import asyncio
import collections.abc as c
import functools
import typing as t
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

import pydantic
import pydantic_core
from frozendict import frozendict


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


class _PydanticFrozenDictAnnotation[_K, _V]:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: t.Any, handler: pydantic.GetCoreSchemaHandler
    ) -> pydantic_core.core_schema.CoreSchema:
        def validate_from_dict(
            d: dict[_K, _V] | frozendict[_K, _V],
        ) -> frozendict[_K, _V]:
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


type FrozenDict[_K, _V] = t.Annotated[
    frozendict[_K, _V], _PydanticFrozenDictAnnotation
]
