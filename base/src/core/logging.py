import logging
import sys
from types import FrameType
from typing import Any

from loguru import logger


class InterceptHandler(logging.Handler):

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record with loguru
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Get caller from where originated the logged message
        frame: FrameType | None = logging.currentframe()
        depth = 2

        if frame:
            while frame.f_code.co_filename == logging.__file__:
                if frame.f_back:
                    frame = frame.f_back
                    depth += 1
                else:
                    break

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: The minimum log level to capture
        json_format: Whether to output logs in JSON format
    """
    # Remove default loguru handler
    logger.remove()

    # Configure log format
    if json_format:
        format_dict = {
            "time": "{time:YYYY-MM-DD HH:mm:ss.SSS}",
            "level": "{level}",
            "message": "{message}",
            "module": "{module}",
            "function": "{function}",
            "line": "{line}",
        }
        log_format = str(format_dict)
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "{message}"
        )

    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        serialize=json_format,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    # Intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level)

    # Remove every other logger's handlers and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True


def configure_logging(settings: Any) -> None:
    """
    Configure logging based on application settings.

    Args:
        settings: Application settings instance
    """
    setup_logging(log_level=settings.LOG_LEVEL, json_format=settings.LOG_FORMAT == "json")
