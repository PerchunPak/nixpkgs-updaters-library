import asyncio
from functools import wraps

import typer


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


skipped_option = typer.Option(parser=lambda _: _, hidden=True, expose_value=False)
