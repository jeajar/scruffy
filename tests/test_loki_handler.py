"""Tests for Loki logging handler."""

import json
import logging
import sys
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scruffy.frameworks_and_drivers.utils.loki_handler import (
    JsonFormatter,
    LokiHandler,
)


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create a JsonFormatter instance."""
        return JsonFormatter()

    @pytest.fixture
    def log_record(self):
        """Create a basic log record."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        return record

    def test_format_basic_message(self, formatter, log_record):
        """Test formatting a basic log message."""
        result = formatter.format(log_record)
        parsed = json.loads(result)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_format_includes_timestamp(self, formatter, log_record):
        """Test that timestamp is included in ISO format."""
        result = formatter.format(log_record)
        parsed = json.loads(result)

        # Should be ISO format with timezone
        assert "T" in parsed["timestamp"]
        assert "+" in parsed["timestamp"] or "Z" in parsed["timestamp"]

    def test_format_error_includes_location(self, formatter):
        """Test that ERROR level includes location info."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Error message",
            args=(),
            exc_info=None,
        )
        record.filename = "file.py"
        record.funcName = "test_function"

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "location" in parsed
        assert parsed["location"]["file"] == "file.py"
        assert parsed["location"]["line"] == 42
        assert parsed["location"]["function"] == "test_function"

    def test_format_info_excludes_location(self, formatter, log_record):
        """Test that INFO level excludes location info."""
        result = formatter.format(log_record)
        parsed = json.loads(result)

        assert "location" not in parsed

    def test_format_with_exception(self, formatter):
        """Test formatting with exception info."""
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="/path/to/file.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Test error" in parsed["exception"]

    def test_format_with_extra_fields(self, formatter):
        """Test formatting with extra fields."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.request_id = 123
        record.user_email = "test@example.com"

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["request_id"] == 123
        assert parsed["user_email"] == "test@example.com"

    def test_format_excludes_reserved_attrs(self, formatter, log_record):
        """Test that reserved attributes are not included in output."""
        result = formatter.format(log_record)
        parsed = json.loads(result)

        # These should not appear as top-level keys
        assert "args" not in parsed
        assert "exc_info" not in parsed
        assert "levelno" not in parsed
        assert "pathname" not in parsed


class TestLokiHandler:
    """Tests for the LokiHandler class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        with patch("scruffy.frameworks_and_drivers.utils.loki_handler.httpx.Client") as mock:
            client_instance = MagicMock()
            mock.return_value = client_instance
            yield client_instance

    @pytest.fixture
    def handler(self, mock_client):
        """Create a LokiHandler instance with mocked client."""
        return LokiHandler(
            url="http://loki:3100/loki/api/v1/push",
            labels={"app": "scruffy", "env": "test"},
        )

    @pytest.fixture
    def log_record(self):
        """Create a basic log record."""
        return logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

    def test_handler_initialization(self, mock_client):
        """Test handler initialization."""
        handler = LokiHandler(
            url="http://loki:3100/loki/api/v1/push",
            labels={"app": "test"},
            timeout=5.0,
        )

        assert handler.url == "http://loki:3100/loki/api/v1/push"
        assert handler.labels == {"app": "test"}
        assert handler.timeout == 5.0

    def test_handler_default_labels(self, mock_client):
        """Test handler uses default labels."""
        handler = LokiHandler(url="http://loki:3100/loki/api/v1/push")
        assert handler.labels == {"app": "scruffy"}

    def test_emit_sends_to_loki(self, handler, mock_client, log_record):
        """Test that emit sends log to Loki."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        handler.emit(log_record)

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args

        assert call_args[0][0] == "http://loki:3100/loki/api/v1/push"
        assert call_args[1]["headers"] == {"Content-Type": "application/json"}

        # Check payload structure
        payload = call_args[1]["json"]
        assert "streams" in payload
        assert len(payload["streams"]) == 1
        stream = payload["streams"][0]
        assert "stream" in stream
        assert "values" in stream

    def test_emit_includes_level_in_labels(self, handler, mock_client, log_record):
        """Test that emit includes log level in stream labels."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        handler.emit(log_record)

        payload = mock_client.post.call_args[1]["json"]
        stream_labels = payload["streams"][0]["stream"]

        assert stream_labels["level"] == "info"
        assert stream_labels["app"] == "scruffy"
        assert stream_labels["env"] == "test"

    def test_emit_formats_timestamp_as_nanoseconds(self, handler, mock_client, log_record):
        """Test that timestamp is in nanoseconds."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        handler.emit(log_record)

        payload = mock_client.post.call_args[1]["json"]
        timestamp = payload["streams"][0]["values"][0][0]

        # Nanosecond timestamp should be a long string of digits
        assert timestamp.isdigit()
        assert len(timestamp) >= 19  # Nanoseconds have at least 19 digits

    def test_emit_handles_http_error(self, handler, mock_client, log_record, capsys):
        """Test that HTTP errors are handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        # Should not raise
        handler.emit(log_record)

        # Should print to stderr
        captured = capsys.readouterr()
        assert "Loki handler HTTP error" in captured.err

    def test_emit_handles_connection_error(self, handler, mock_client, log_record, capsys):
        """Test that connection errors are handled gracefully."""
        mock_client.post.side_effect = httpx.RequestError("Connection refused")

        # Should not raise
        handler.emit(log_record)

        # Should print to stderr
        captured = capsys.readouterr()
        assert "Loki handler connection error" in captured.err

    def test_close_closes_client(self, handler, mock_client):
        """Test that close() closes the HTTP client."""
        handler.close()
        mock_client.close.assert_called_once()


class TestLokiHandlerIntegration:
    """Integration tests for LokiHandler with actual logging."""

    @pytest.fixture(autouse=True)
    def cleanup_logging(self):
        """Clean up logging after each test."""
        yield
        root = logging.getLogger()
        root.handlers.clear()
        logging.Logger.manager.loggerDict.clear()

    def test_handler_with_logger(self):
        """Test handler works with Python logger."""
        with patch("scruffy.frameworks_and_drivers.utils.loki_handler.httpx.Client") as mock:
            client_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            client_instance.post.return_value = mock_response
            mock.return_value = client_instance

            handler = LokiHandler(url="http://loki:3100/loki/api/v1/push")
            logger = logging.getLogger("test.integration")
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

            logger.info("Integration test message", extra={"request_id": 42})

            client_instance.post.assert_called_once()
            payload = client_instance.post.call_args[1]["json"]
            log_message = payload["streams"][0]["values"][0][1]
            parsed = json.loads(log_message)

            assert parsed["message"] == "Integration test message"
            assert parsed["request_id"] == 42


class TestLokiHandlerRecursionPrevention:
    """Tests for recursion prevention in LokiHandler."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        with patch("scruffy.frameworks_and_drivers.utils.loki_handler.httpx.Client") as mock:
            client_instance = MagicMock()
            mock.return_value = client_instance
            yield client_instance

    @pytest.fixture
    def handler(self, mock_client):
        """Create a LokiHandler instance with mocked client."""
        return LokiHandler(url="http://loki:3100/loki/api/v1/push")

    def test_ignores_httpx_logs(self, handler, mock_client):
        """Test that logs from httpx are ignored to prevent recursion."""
        record = logging.LogRecord(
            name="httpx",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="HTTP Request: POST http://loki:3100/loki/api/v1/push",
            args=(),
            exc_info=None,
        )

        handler.emit(record)

        # Should not have called post since httpx logs are ignored
        mock_client.post.assert_not_called()

    def test_ignores_httpcore_logs(self, handler, mock_client):
        """Test that logs from httpcore are ignored."""
        record = logging.LogRecord(
            name="httpcore.connection",
            level=logging.DEBUG,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Connection established",
            args=(),
            exc_info=None,
        )

        handler.emit(record)
        mock_client.post.assert_not_called()

    def test_ignores_urllib3_logs(self, handler, mock_client):
        """Test that logs from urllib3 are ignored."""
        record = logging.LogRecord(
            name="urllib3.connectionpool",
            level=logging.DEBUG,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Starting new HTTP connection",
            args=(),
            exc_info=None,
        )

        handler.emit(record)
        mock_client.post.assert_not_called()

    def test_allows_application_logs(self, handler, mock_client):
        """Test that application logs are still processed."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        record = logging.LogRecord(
            name="scruffy.use_cases.process_media",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Processing media",
            args=(),
            exc_info=None,
        )

        handler.emit(record)
        mock_client.post.assert_called_once()

    def test_reentrant_emit_is_blocked(self, handler, mock_client):
        """Test that re-entrant calls to emit are blocked."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Simulate re-entrancy by setting the flag
        handler._emitting = True
        handler.emit(record)

        # Should not have called post since we're already emitting
        mock_client.post.assert_not_called()

    def test_emitting_flag_reset_after_emit(self, handler, mock_client):
        """Test that _emitting flag is reset after emit completes."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        assert handler._emitting is False
        handler.emit(record)
        assert handler._emitting is False

    def test_emitting_flag_reset_on_error(self, handler, mock_client):
        """Test that _emitting flag is reset even when an error occurs."""
        mock_client.post.side_effect = httpx.RequestError("Connection refused")

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        assert handler._emitting is False
        handler.emit(record)
        assert handler._emitting is False
