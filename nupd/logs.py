import enum

from loguru import logger
from rich.text import Text

from nupd import utils


class LoggingLevel(enum.Enum):
    TRACE = "trace"
    """Use only for tracing error without a debugger."""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def as_int(self) -> int:
        return {
            "trace": 5,
            "debug": 10,
            "info": 20,
            "success": 25,
            "warning": 30,
            "error": 40,
            "critical": 50,
        }[self.value]


def setup_logging(log_level: LoggingLevel) -> None:
    logger.remove()
    _ = logger.add(
        lambda s: utils.console.print(Text.from_ansi(s)),
        level=log_level.as_int(),
        colorize=utils.console.is_terminal,
        backtrace=True,
        diagnose=True,
    )
    logger.debug("Logging was setup!")
