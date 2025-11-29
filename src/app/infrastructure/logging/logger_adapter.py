"""Standard Logging Adapter.

Implements LoggingPort using Python's standard logging module.
"""

import logging
from typing import Any


class StandardLoggingAdapter:
    """Adapter implementing LoggingPort using standard logging.

    Wraps a standard library Logger and provides the LoggingPort
    interface with structured context support via the `extra` parameter.

    Example:
        >>> logger = StandardLoggingAdapter(logging.getLogger("myapp"))
        >>> logger.info("User logged in", user_id="123", ip="192.168.1.1")

    The context kwargs are passed as `extra` to the underlying logger,
    which can be formatted using a custom Formatter.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the logging adapter.

        Args:
            logger: Standard library Logger instance.
        """
        self._logger = logger

    @property
    def name(self) -> str:
        """Return the logger name."""
        return self._logger.name

    def _format_message(self, msg: str, context: dict[str, Any]) -> str:
        """Format message with context for logging.

        Args:
            msg: The log message.
            context: Additional context key-value pairs.

        Returns:
            Formatted message string with context appended.
        """
        if not context:
            return msg
        ctx_str = " ".join(f"{k}={v}" for k, v in context.items())
        return f"{msg} | {ctx_str}"

    def info(self, msg: str, **context: Any) -> None:
        """Log an informational message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        self._logger.info(
            self._format_message(msg, context),
            extra=context,
        )

    def warning(self, msg: str, **context: Any) -> None:
        """Log a warning message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        self._logger.warning(
            self._format_message(msg, context),
            extra=context,
        )

    def error(self, msg: str, **context: Any) -> None:
        """Log an error message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        self._logger.error(
            self._format_message(msg, context),
            extra=context,
        )

    def debug(self, msg: str, **context: Any) -> None:
        """Log a debug message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        self._logger.debug(
            self._format_message(msg, context),
            extra=context,
        )

    def critical(self, msg: str, **context: Any) -> None:
        """Log a critical error message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        self._logger.critical(
            self._format_message(msg, context),
            extra=context,
        )
