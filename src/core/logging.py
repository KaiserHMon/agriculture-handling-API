import logging
import random
import sys
from pathlib import Path
from types import FrameType
from typing import Any

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Intercepts logs from standard logging and redirects them to loguru.

    :param:
        logging: The logging module
    """

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


def should_log(record) -> bool:
    """
    Implement log sampling for high-frequency paths.

    :param record: Log record to evaluate
    :return: Whether the record should be logged
    """
    # Sample health check endpoints
    if record["name"] == "src.api.health":
        return random.random() < 0.1  # Log only 10% of health checks

    # Sample SQL queries in DEBUG level
    if record["level"].name == "DEBUG" and "sql" in record["name"].lower():
        return random.random() < 0.05  # Log only 5% of SQL queries

    return True


def setup_logging(
    log_level: str = "INFO", json_format: bool = True, module_levels: dict[str, str] | None = None
) -> None:
    """
    Configure logging for the application.

    :param:
        log_level: The minimum log level to capture
        json_format: Whether to output logs in JSON format
        module_levels: Dictionary of module-specific log levels
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
            "process": "{process}",
            "thread": "{thread}",
        }
        log_format = str(format_dict)
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "{message}"
        )

    # Ensure logs directory exists
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)

    # Add console handler with sampling
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        serialize=json_format,
        backtrace=True,
        diagnose=True,
        enqueue=True,
        filter=should_log,
    )

    # Add file handler with rotation
    logger.add(
        "logs/app_{time}.log",
        format=log_format,
        level=log_level,
        serialize=json_format,
        rotation="100 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
        filter=should_log,
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

    params:
        settings: Application settings instance
    """
    setup_logging(
        log_level=settings.LOG_LEVEL,
        json_format=settings.LOG_FORMAT == "json",
        module_levels=settings.LOG_MODULE_LEVELS,
    )

    # Apply module-specific log levels
    if settings.LOG_MODULE_LEVELS:
        for module, level in settings.LOG_MODULE_LEVELS.items():
            logging.getLogger(module).setLevel(level)
