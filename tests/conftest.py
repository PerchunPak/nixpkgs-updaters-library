from pathlib import Path

import inject
import pytest

from nupd.injections import Config, inject_configure


@pytest.fixture(scope="session", autouse=True)
def configure_injections() -> None:
    inject.configure(
        inject_configure(
            Config(
                nixpkgs_path=Path.cwd(),
                input_file="/homeless-shelter",
                output_file="/homeless-shelter",
                jobs=10,
            )
        )
    )
