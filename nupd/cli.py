import typing as t
from pathlib import Path

import inject
import typer

import nupd.logging
from nupd.injections import Config, inject_configure
from nupd.utils import coro, skipped_option

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
    ] = Path.cwd(),
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
        int | None,
        typer.Option(
            "--jobs",
            "-j",
            help="Limit for concurrent jobs.",
            show_default="automatically",
        ),
    ] = None,
    log_level: nupd.logging.LoggingLevel = nupd.logging.LoggingLevel.INFO.value,
) -> None:
    """A boilerplate-less updater for Nixpkgs ecosystems."""
    inject.configure(
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


@app.command()
@coro
async def update() -> None:
    """Update an entry (or multiple)."""
    raise NotImplementedError


if __name__ == "__main__":
    app()
