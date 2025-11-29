"""Tests for StandardLoggingAdapter.

Verifies the logging adapter properly implements LoggingPort
and delegates to the standard library logger.
"""

import logging
from unittest.mock import MagicMock

import pytest

from src.app.infrastructure.logging.logger_adapter import StandardLoggingAdapter


class TestStandardLoggingAdapter:
    """Tests for StandardLoggingAdapter."""

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """Create a mock logger for testing."""
        return MagicMock(spec=logging.Logger)

    @pytest.fixture
    def adapter(self, mock_logger: MagicMock) -> StandardLoggingAdapter:
        """Create adapter with mock logger."""
        return StandardLoggingAdapter(mock_logger)

    def test_info_logs_message(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Info method logs at INFO level."""
        adapter.info("Test message")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Test message" in call_args[0][0]

    def test_info_includes_context(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Info method includes context in message."""
        adapter.info("Test message", user_id="123", action="login")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        message = call_args[0][0]
        assert "user_id=123" in message
        assert "action=login" in message

    def test_warning_logs_message(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Warning method logs at WARNING level."""
        adapter.warning("Warning message", code=42)

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "Warning message" in call_args[0][0]
        assert "code=42" in call_args[0][0]

    def test_error_logs_message(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Error method logs at ERROR level."""
        adapter.error("Error occurred", error="Connection failed")

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Error occurred" in call_args[0][0]
        assert "error=Connection failed" in call_args[0][0]

    def test_debug_logs_message(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Debug method logs at DEBUG level."""
        adapter.debug("Debug info", details="extra data")

        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        assert "Debug info" in call_args[0][0]

    def test_critical_logs_message(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Critical method logs at CRITICAL level."""
        adapter.critical("System failure", component="database")

        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args
        assert "System failure" in call_args[0][0]

    def test_message_without_context(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Message without context is logged cleanly."""
        adapter.info("Simple message")

        call_args = mock_logger.info.call_args
        assert call_args[0][0] == "Simple message"

    def test_name_property(self, mock_logger: MagicMock) -> None:
        """Name property returns logger name."""
        mock_logger.name = "test.logger"
        adapter = StandardLoggingAdapter(mock_logger)

        assert adapter.name == "test.logger"

    def test_extra_parameter_passed(
        self, adapter: StandardLoggingAdapter, mock_logger: MagicMock
    ) -> None:
        """Context is passed as extra to underlying logger."""
        adapter.info("Test", foo="bar")

        call_args = mock_logger.info.call_args
        assert call_args[1]["extra"] == {"foo": "bar"}

    def test_with_real_logger(self, caplog: pytest.LogCaptureFixture) -> None:
        """Adapter works with real logger."""
        real_logger = logging.getLogger("test.adapter")
        adapter = StandardLoggingAdapter(real_logger)

        with caplog.at_level(logging.INFO):
            adapter.info("Real log test", request_id="abc123")

        assert "Real log test" in caplog.text
        assert "request_id=abc123" in caplog.text
