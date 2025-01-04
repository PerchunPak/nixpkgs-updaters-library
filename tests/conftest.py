import collections.abc as c
import sys
import typing as t
from pathlib import Path

import inject
import pytest
from aioresponses import aioresponses
from loguru import logger
from pytest_mock import MockerFixture

from nupd.cache import Cache
from nupd.injections import Config, inject_configure
from nupd.logs import LoggingLevel


@pytest.fixture(scope="session", autouse=True)
def configure_injections() -> None:
    _ = inject.configure(
        inject_configure(
            config=Config(
                nixpkgs_path=Path.cwd(),
                input_file=None,
                output_file=None,
                jobs=1,
            ),
            classes=None,  # pyright: ignore[reportArgumentType]
            cache=Cache(),
        ),
        clear=True,
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


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--loguru-log-level",
        action="store",
        default="debug",
        choices=[level.value for level in LoggingLevel],
    )


@pytest.fixture(scope="session", autouse=True)
def configure_loguru(request: pytest.FixtureRequest) -> None:
    log_level = request.config.getoption("--loguru-log-level")
    logger.remove()
    _ = logger.add(
        sys.stdout,
        level=LoggingLevel(log_level).as_int(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )


T = t.TypeVar("T")
type MOCK_INJECT = c.Callable[[type[T], T], None]  # pyright: ignore[reportGeneralTypeIssues]


@pytest.fixture
def mock_inject(mocker: MockerFixture) -> MOCK_INJECT:
    def wrapped[T](type_: type[T], value: T) -> None:
        real_impl = inject.instance

        def my_impl(
            type_to_get: type[t.Any], *args: t.Any, **kwargs: t.Any
        ) -> t.Any:
            if type_to_get == type_:
                return value
            return real_impl(type_to_get, *args, **kwargs)

        _ = mocker.patch("inject.instance", my_impl)

    return wrapped
