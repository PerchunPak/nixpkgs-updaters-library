import typing as t
from pathlib import Path

import inject
from attrs import define


@define
class Config:
    nixpkgs_path: Path
    input_file: Path | None
    output_file: Path | None
    jobs: int


def inject_configure(config: Config) -> t.Callable[[inject.Binder], None]:
    def wrapped(binder: inject.Binder) -> None:
        _ = binder.bind(Config, config)

    return wrapped
