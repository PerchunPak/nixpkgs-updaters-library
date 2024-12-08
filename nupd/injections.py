import typing as t
from pathlib import Path

import inject
from attrs import define

from nupd.cache import Cache
from nupd.models import ImplClasses


@define
class Config:
    nixpkgs_path: Path
    input_file: Path | None
    output_file: Path | None
    jobs: int


def inject_configure(
    config: Config, classes: ImplClasses, cache: Cache
) -> t.Callable[[inject.Binder], None]:
    def wrapped(binder: inject.Binder) -> None:
        _ = binder.bind(Config, config)
        _ = binder.bind(ImplClasses, classes)
        _ = binder.bind(Cache, cache)

    return wrapped
