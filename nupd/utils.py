from __future__ import annotations

import asyncio
import collections.abc as c
import functools
import typing as t
from concurrent.futures import ThreadPoolExecutor
from functools import wraps


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
