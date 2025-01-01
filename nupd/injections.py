import typing as t
from pathlib import Path

import inject
from attrs import define

from nupd.cache import Cache
from nupd.models import ImplClasses
from nupd.shutdown import Shutdowner


@define
class Config:
    nixpkgs_path: Path
    input_file: Path | None
    output_file: Path | None
    jobs: int


def inject_configure(
    config: Config,
    classes: ImplClasses,
    cache: Cache,
    shutdowner: Shutdowner | None = None,
) -> t.Callable[[inject.Binder], None]:
    def wrapped(binder: inject.Binder) -> None:
        _ = binder.bind(Config, config)
        _ = binder.bind(ImplClasses, classes)
        _ = binder.bind(Cache, cache)
        _ = binder.bind(Shutdowner, shutdowner if shutdowner else Shutdowner())

    return wrapped
