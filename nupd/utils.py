import asyncio
import collections.abc as c
import typing as t
from functools import wraps

import typer.models


def coro[R](
    f: c.Callable[..., c.Coroutine[t.Any, t.Any, R]],
) -> c.Callable[..., R]:
    @wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> R:  # pyright: ignore[reportAny]
        return asyncio.run(f(*args, **kwargs))

    return wrapper


skipped_option: typer.models.OptionInfo = typer.Option(
    parser=lambda _: _, hidden=True, expose_value=False
)


def chunks[T](lst: c.Sequence[T], n: int) -> c.Iterable[c.Sequence[T]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
