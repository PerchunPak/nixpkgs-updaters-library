import collections.abc as c
import functools
import typing as t
from pathlib import Path

import inject
import typer

import nupd.logging
from nupd import utils
from nupd.injections import Config, inject_configure


def callback[F: c.Callable[..., t.Any]](func: F) -> F:
    patched = utils.patch_signature(
        func,
        """
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
            ),
        ] = 32,
        log_level: LoggingLevel = LoggingLevel.INFO
        """,
        globals={
            "t": t,
            "typer": typer,
            "Path": Path,
            "LoggingLevel": nupd.logging.LoggingLevel,
        },
    )

    @functools.wraps(patched)
    def callback(  # pyright: ignore[reportAny]
        nixpkgs_path: Path,
        input_file: Path | None,
        output_file: Path | None,
        jobs: int,
        log_level: nupd.logging.LoggingLevel,
        *args: t.Any,  # pyright: ignore[reportAny]
        **kwargs: t.Any,  # pyright: ignore[reportAny]
    ) -> t.Any:
        print("callback")
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
        nupd.logging.setup_logging(log_level)
        return patched(*args, **kwargs)  # pyright: ignore[reportAny]

    return callback  # pyright: ignore[reportReturnType]


def add[F: c.Callable[..., t.Any]](func: F) -> F:
    patched = utils.patch_signature(
        func,
        """
        entry_ids: t.Annotated[
            list[str],
            typer.Argument(
                help="Entries to add",
                show_default=False,
            ),
        ]
        """,
        globals={"t": t, "typer": typer},
    )

    @functools.wraps(patched)
    def wrapped(_entry_ids: t.Any, *a: t.Any, **kw: t.Any) -> t.Any:  # pyright: ignore[reportAny]
        return patched(*a, **kw, entry_ids=_entry_ids)  # pyright: ignore[reportAny]

    return wrapped  # pyright: ignore[reportReturnType]


def update[F: c.Callable[..., t.Any]](func: F) -> F:
    patched = utils.patch_signature(
        func,
        """
        _entry_ids: t.Annotated[
            list[str] | None,
            typer.Argument(
                help="Entries to add",
                show_default="all entries",
            ),
        ]
        """,
        globals={"t": t, "typer": typer},
    )

    @functools.wraps(patched)
    def wrapped(_entry_ids: t.Any, *a: t.Any, **kw: t.Any) -> t.Any:  # pyright: ignore[reportAny]
        return patched(*a, **kw, entry_ids=_entry_ids)  # pyright: ignore[reportAny]

    return wrapped  # pyright: ignore[reportReturnType]
