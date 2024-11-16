"""Module for some useful utils."""
import os
import pathlib
import sys
import typing as t

import apykuma
import sentry_sdk
from loguru import logger

BASE_DIR = pathlib.Path(__file__).parent.parent
DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))


class Singleton(type):
    """Metaclass to do Singleton pattern."""

    _instances: dict[type, t.Any] = {}  # type: ignore[misc] # Explicit "Any" is not allowed

    def __call__(cls, *args, **kwargs) -> t.Any:  # type: ignore[misc] # Explicit "Any" is not allowed
        """Actual logic in this class.

        See https://stackoverflow.com/a/6798042.
        """
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)

            if hasattr(instance, "_setup"):
                instance = instance._setup()
            cls._instances[cls] = instance

        return cls._instances[cls]


def setup_logging() -> None:
    """Setup logging for the addon."""
    from src import config as config_module  # circular import

    config = config_module.Config()

    logger.remove()
    if config.logging.level < config_module.LoggingLevel.WARNING:
        logger.add(
            sys.stdout,
            level=config.logging.level,
            filter=lambda record: record["level"].no < config_module.LoggingLevel.WARNING,
            colorize=True,
            serialize=config.logging.json,
            backtrace=True,
            diagnose=True,
        )
    logger.add(
        sys.stderr,
        level=config.logging.level,
        filter=lambda record: record["level"].no >= config_module.LoggingLevel.WARNING,
        colorize=True,
        serialize=config.logging.json,
        backtrace=True,
        diagnose=True,
    )
    logger.debug("Logging was setup!")


def start_sentry() -> None:
    """Start Sentry listening."""
    # circular imports
    from src.config import Config

    config = Config()

    if not config.sentry.enabled:
        return

    sentry_sdk.init(
        dsn=config.sentry.dsn,
        traces_sample_rate=config.sentry.traces_sample_rate,
        release=_get_commit(BASE_DIR / "commit.txt"),
        environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
        _experiments={
            "profiles_sample_rate": 1.0,
        },
    )


def _get_commit(commit_txt_path: pathlib.Path) -> t.Optional[str]:
    """Get current commit from ``commit.txt`` file."""
    if not commit_txt_path.exists():
        return None

    with commit_txt_path.open() as commit_txt_file:
        commit = commit_txt_file.read().strip()
        return commit


async def start_apykuma() -> None:
    # circular imports
    from src.config import Config

    config = Config()

    if not config.apykuma.enabled:
        return

    await apykuma.start(
        url=config.apykuma.url,
        interval=config.apykuma.interval,
        delay=config.apykuma.delay,
        handle_exception=logger.exception,
    )
