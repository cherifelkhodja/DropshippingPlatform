"""Logging Configuration.

Provides centralized logging configuration for the application.
"""

import logging
import sys
from typing import Literal


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(
    level: str = "INFO",
    format_style: Literal["simple", "detailed"] = "simple",
) -> None:
    """Configure application-wide logging.

    Sets up the root logger with consistent formatting and level.
    Should be called once at application startup.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_style: Format style - 'simple' for basic, 'detailed' for more info.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if format_style == "detailed":
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | "
            "%(message)s"
        )
    else:
        log_format = LOG_FORMAT

    # Create formatter
    formatter = logging.Formatter(fmt=log_format, datefmt=DATE_FORMAT)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add stream handler (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Configure specific loggers
    # Reduce noise from third-party libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if level.upper() == "DEBUG" else logging.WARNING
    )

    # Celery logger configuration
    logging.getLogger("celery").setLevel(log_level)
    logging.getLogger("celery.task").setLevel(log_level)
    logging.getLogger("celery.worker").setLevel(log_level)

    logging.info(
        "Logging configured",
        extra={"level": level, "format_style": format_style},
    )
