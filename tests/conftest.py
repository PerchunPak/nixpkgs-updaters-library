import collections.abc as c
from pathlib import Path

import inject
import pytest
from aioresponses import aioresponses
from pytest_mock import MockerFixture

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


@pytest.fixture
def mock_aiohttp() -> c.Iterable[aioresponses]:
    with aioresponses() as m:
        yield m


@pytest.fixture(scope="session", autouse=True)
def mock_cache_dir(
    session_mocker: MockerFixture, tmpdir_factory: pytest.TempPathFactory
) -> None:
    _ = session_mocker.patch(
        "platformdirs.user_cache_dir",
        return_value=str(tmpdir_factory.mktemp("cache")),
    )
