from pathlib import Path

import inject
import pytest

from nupd.injections import Config, inject_configure


@pytest.fixture(scope="session", autouse=True)
def configure_injections() -> None:
    _ = inject.configure(
        inject_configure(
            config=Config(
                nixpkgs_path=Path.cwd(),
                input_file=Path("/homeless-shelter"),
                output_file=Path("/homeless-shelter"),
                jobs=10,
            ),
            classes=None,  # pyright: ignore[reportArgumentType]
        )
    )
