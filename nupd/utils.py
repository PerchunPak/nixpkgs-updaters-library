from __future__ import annotations

import asyncio
import collections.abc as c
import functools
import types
import typing as t
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import wraps

import typer.models

if t.TYPE_CHECKING:
    import attrs


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


skipped_option: typer.models.OptionInfo = typer.Option(  # pragma: no cover
    parser=lambda _: _, hidden=True, expose_value=False
)


def chunks[T](lst: c.Sequence[T], n: int) -> c.Iterable[c.Sequence[T]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def json_transformer(
    _cls: type[attrs.AttrsInstance], fields: list[attrs.Attribute[t.Any]]
) -> list[t.Any]:
    """https://www.attrs.org/en/stable/extending.html#automatic-field-transformation-and-modification."""
    results: list[t.Any] = []

    for field in fields:
        if field.converter is not None:
            results.append(field)
            continue

        if field.type in {datetime, "datetime"} or (
            type(field.type) in {t.Union, types.UnionType}  # pyright: ignore[reportDeprecated]
            and datetime in t.get_args(field.type)
        ):
            converter: t.Callable[[str | t.Any], datetime | t.Any] | None = (
                lambda d: datetime.fromisoformat(d) if isinstance(d, str) else d
            )
        else:
            converter = None

        results.append(field.evolve(converter=converter))
    return results


def json_serialize(
    _cls: type[attrs.AttrsInstance],
    _field: attrs.Attribute[t.Any],
    value: t.Any,
) -> t.Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, c.Iterable) and not isinstance(value, str):
        return list(value)
    return value
