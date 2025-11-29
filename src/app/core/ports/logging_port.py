"""Logging Port.

Interface for structured logging operations.
"""

from typing import Protocol, Any


class LoggingPort(Protocol):
    """Port interface for logging operations.

    This port defines the contract for structured logging.
    Implementations will handle the actual logging infrastructure
    (e.g., structlog, standard logging, cloud logging services).
    """

    def info(self, msg: str, **context: Any) -> None:
        """Log an informational message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        ...

    def warning(self, msg: str, **context: Any) -> None:
        """Log a warning message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        ...

    def error(self, msg: str, **context: Any) -> None:
        """Log an error message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        ...

    def debug(self, msg: str, **context: Any) -> None:
        """Log a debug message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        ...

    def critical(self, msg: str, **context: Any) -> None:
        """Log a critical error message.

        Args:
            msg: The log message.
            **context: Additional context key-value pairs.
        """
        ...
