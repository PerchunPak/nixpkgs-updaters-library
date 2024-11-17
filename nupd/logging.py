import enum

import loguru


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
    if log_level < LoggingLevel.WARNING:
        logger.add(
            sys.stdout,
            level=log_level.value,
            filter=lambda record: record["level"].no < LoggingLevel.WARNING,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    logger.add(
        sys.stderr,
        level=log_level,
        filter=lambda record: record["level"].no >= LoggingLevel.WARNING,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    logger.debug("Logging was setup!")
