import asyncio
import collections.abc as c
import inspect
import typing as t
from functools import wraps

import typer.models

from nupd.format_signature import format_signature


def coro[R](f: c.Callable[..., c.Coroutine[t.Any, t.Any, R]]) -> c.Callable[..., R]:
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


def patch_signature[F: t.Callable[..., t.Any]](
    func: F,
    additional_code: str,
    *,
    globals: dict[str, t.Any],
) -> F:
    signature = inspect.signature(func)
    as_str = format_signature(signature)
    as_str = as_str.removeprefix("(")

    locals: dict[str, t.Any] = {}
    exec(
        f"def THIS_IS_ILLEGAL({additional_code}, {as_str}: ...",
        globals,
        locals,
    )
    func.__wrapped__ = locals["THIS_IS_ILLEGAL"]  # pyright: ignore[reportFunctionMemberAccess]

    return func
