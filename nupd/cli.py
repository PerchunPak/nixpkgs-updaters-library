import typing as t
from pathlib import Path

import inject
import typer

import nupd.logs
from nupd.injections import Config, inject_configure
from nupd.utils import coro

app = typer.Typer()


@app.callback()
def callback(
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
    ] = Path.cwd(),  # pyright: ignore[reportCallInDefaultInitializer]
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
    """A boilerplate-less updater for Nixpkgs ecosystems."""
    nupd.logs.setup_logging(log_level)
    _ = inject.configure(
        inject_configure(
            Config(
                nixpkgs_path=nixpkgs_path,
                input_file=input_file,
                output_file=output_file,
                jobs=jobs,
            )
        )
    )


@app.command()
@coro
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
    config = inject.instance(Config)
    print(config.nixpkgs_path)
    print(entry_ids)


@app.command()
@coro
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
    print(entry_ids)
    raise NotImplementedError


if __name__ == "__main__":
    app()
