import typing as t
from pathlib import Path

import inject
import typer
from loguru import logger

import nupd.logs
from nupd.base import Nupd
from nupd.cache import Cache
from nupd.injections import Config, inject_configure
from nupd.models import ImplClasses
from nupd.shutdown import Shutdowner
from nupd.utils import async_to_sync

app = typer.Typer(context_settings={})
_CWD = Path.cwd()


@app.callback()
def callback(
    ctx: typer.Context,
    nixpkgs_path: t.Annotated[
        Path,
        typer.Option(
            "--nixpkgs-path",
            "-N",
            help="Path to nixpkgs",
            show_default="current directory",
            exists=True,
            file_okay=False,
            writable=True,
        ),
    ] = _CWD,
    input_file: t.Annotated[
        Path | None,
        typer.Option(
            "--input-file",
            "-i",
            help="The input file with information about entries.",
            show_default="automatically",
            writable=True,
        ),
    ] = None,
    output_file: t.Annotated[
        Path | None,
        typer.Option(
            "--output-file",
            "-o",
            help="The output file with information about entries.",
            show_default="automatically",
            writable=True,
        ),
    ] = None,
    jobs: t.Annotated[
        int,
        typer.Option(
            "--jobs",
            "-j",
            help="Limit for concurrent jobs.",
        ),
    ] = 32,
    log_level: nupd.logs.LoggingLevel = nupd.logs.LoggingLevel.INFO.value,  # pyright: ignore[reportArgumentType] # typer requires string here
) -> None:
    """A boilerplate-less updater library for Nixpkgs ecosystems."""
    nupd.logs.setup_logging(log_level)
    if not isinstance(ctx.obj, ImplClasses):
        logger.error(
            "You have to provide your implementation of `ABCBase`, `Entry`"
            " and `EntryInfo` using `app.info.context_settings`. Please see"
            " `example` directory."
        )
        raise typer.Exit(1)

    _ = inject.configure(
        inject_configure(
            config=Config(
                nixpkgs_path=nixpkgs_path,
                input_file=input_file,
                output_file=output_file,
                jobs=jobs,
            ),
            classes=ctx.obj,
            cache=Cache(),
        ),
        allow_override=True,
    )


@app.command()
@async_to_sync
async def add(
    entry_ids: t.Annotated[
        list[str],
        typer.Argument(
            help="Entries to add",
            show_default=False,
        ),
    ],
) -> None:
    """Add a new entry (or multiple)."""
    try:
        await Nupd().add_cmd(entry_ids)
    finally:
        await inject.instance(Shutdowner).shutdown()


@app.command()
@async_to_sync
async def update(
    entry_ids: t.Annotated[
        list[str] | None,
        typer.Argument(
            help="Entries to add",
            show_default="all entries",
        ),
    ] = None,
) -> None:
    """Update an entry (or multiple)."""
    try:
        await Nupd().update_cmd(entry_ids)
    finally:
        await inject.instance(Shutdowner).shutdown()


if __name__ == "__main__":
    app()
