import typing as t
from pathlib import Path

import inject

from nupd.models import ImplClasses, NupdModel
from nupd.shutdown import Shutdowner


class Config(NupdModel, frozen=True):
    nixpkgs_path: Path
    input_file: Path | None
    output_file: Path | None
    jobs: int


def inject_configure(
    config: Config,
    classes: ImplClasses,
    shutdowner: Shutdowner | None = None,
) -> t.Callable[[inject.Binder], None]:
    def wrapped(binder: inject.Binder) -> None:
        _ = binder.bind(Config, config)
        _ = binder.bind(ImplClasses, classes)
        _ = binder.bind(Shutdowner, shutdowner if shutdowner else Shutdowner())

    return wrapped
