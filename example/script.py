import typing as t

import inject
import typer

from nupd import cli1, utils
from nupd.injections import Config

app = typer.Typer()


@app.callback()
@cli1.callback
def callback(hi: str = "Hello") -> None:
    print("lox2")


@app.command()
@cli1.add
@utils.coro
async def add(entry_ids) -> None:
    config = inject.instance(Config)
    print(config.nixpkgs_path)


@app.command()
@cli1.update
@utils.coro
async def update(
    entry_ids: t.Annotated[list[str] | None, utils.skipped_option] = None,
) -> None:
    """Update an entry (or multiple)."""
    raise NotImplementedError


if __name__ == "__main__":
    app()
