import typing as t
from pathlib import Path

import cyclopts
import inject
from loguru import logger

import nupd.logs
from nupd import utils
from nupd.base import Nupd
from nupd.injections import Config, inject_configure
from nupd.models import ImplClasses
from nupd.shutdown import Shutdowner
from nupd.utils import register_implementation_classes

app = cyclopts.App(console=utils.console)
_CWD = Path.cwd()


@app.meta.default
def callback(
    *tokens: t.Annotated[
        str, cyclopts.Parameter(show=False, allow_leading_hyphen=True)
    ],
    nixpkgs_path: t.Annotated[
        cyclopts.types.ResolvedExistingDirectory,
        cyclopts.Parameter(
            alias="-N",
            help="Path to nixpkgs",
        ),
    ] = _CWD,
    input_file: t.Annotated[
        cyclopts.types.ResolvedFile | None,
        cyclopts.Parameter(
            alias="-i",
            help="The input file with information about entries.",
        ),
    ] = None,
    output_file: t.Annotated[
        cyclopts.types.ResolvedFile | None,
        cyclopts.Parameter(
            alias="-o",
            help="The output file with information about entries.",
        ),
    ] = None,
    jobs: t.Annotated[
        int,
        cyclopts.Parameter(alias="-j", help="Limit for concurrent jobs."),
    ] = 32,
    log_level: nupd.logs.LoggingLevel = nupd.logs.LoggingLevel.INFO,
) -> None:
    """Boilerplate-less updater library for Nixpkgs ecosystems."""
    # TODO: this gets called when no argument is supplied
    nupd.logs.setup_logging(log_level)

    impl_classes = register_implementation_classes.impl  # pyright: ignore[reportFunctionMemberAccess]
    if not isinstance(impl_classes, ImplClasses):
        logger.error(
            "You have to provide your implementation of `ABCBase`, `Entry`"
            + " and `EntryInfo` using `register_implementation_classes`. "
            + "Please see the `example` directory."
        )
        return

    _ = inject.configure(
        inject_configure(
            config=Config(
                nixpkgs_path=nixpkgs_path,
                input_file=input_file,
                output_file=output_file,
                jobs=jobs,
            ),
            classes=impl_classes,
        ),
        allow_override=True,
    )

    app(tokens)


@app.command()
@logger.catch
async def add(
    entry_ids: t.Annotated[
        list[str],
        cyclopts.Parameter(help="Entries to add"),
    ],
) -> None:
    """Add a new entry (or multiple)."""
    try:
        await Nupd().add_cmd(entry_ids)
    finally:
        await inject.instance(Shutdowner).shutdown()


@app.command()
@logger.catch
async def update(
    entry_ids: t.Annotated[
        list[str] | None,
        cyclopts.Parameter(
            help="Entries to update",
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
