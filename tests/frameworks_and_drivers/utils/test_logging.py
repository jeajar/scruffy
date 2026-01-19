"""Tests for logging configuration and utilities."""

import logging
import logging.handlers

import pytest

from scruffy.frameworks_and_drivers.utils.logging import (
    configure_logging,
    get_logger,
    reset_logging,
    setup_logger,
)


@pytest.fixture(autouse=True)
def cleanup_logging():
    """Clean up logging configuration after each test."""
    yield
    reset_logging()


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path."""
    return tmp_path / "test.log"


class TestSetupLogger:
    """Tests for the legacy setup_logger function."""

    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger("test")

        assert logger.name == "test"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 0

    def test_setup_logger_with_file(self, temp_log_file):
        """Test logger with file handler."""
        logger = setup_logger("test", log_file=temp_log_file)

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.handlers.RotatingFileHandler)
        assert logger.handlers[0].baseFilename == str(temp_log_file)
        assert logger.handlers[0].maxBytes == 10_000_000
        assert logger.handlers[0].backupCount == 5

    def test_setup_logger_custom_level(self):
        """Test logger with custom level."""
        logger = setup_logger("test", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_logger_writes_to_file(self, temp_log_file):
        """Test that logger writes to file."""
        logger = setup_logger("test", log_file=temp_log_file)
        test_message = "Test log message"

        logger.info(test_message)

        assert temp_log_file.exists()
        log_content = temp_log_file.read_text()
        assert test_message in log_content

    def test_logger_rotating_file(self, temp_log_file):
        """Test rotating file handler configuration."""
        logger = setup_logger("test", log_file=temp_log_file)
        handler = logger.handlers[0]

        assert isinstance(handler, logging.handlers.RotatingFileHandler)
        assert handler.maxBytes == 10_000_000
        assert handler.backupCount == 5

    def test_setup_logger_invalid_level(self):
        """Test that invalid level raises ValueError."""
        with pytest.raises(ValueError):
            setup_logger("test", level="INVALID")


class TestConfigureLogging:
    """Tests for the configure_logging function."""

    def test_configure_logging_basic(self):
        """Test basic logging configuration."""
        configure_logging(level="INFO")
        logger = get_logger("test")

        assert logger.name == "test"
        # Root logger should have handlers
        root = logging.getLogger()
        assert len(root.handlers) >= 1

    def test_configure_logging_with_file(self, temp_log_file):
        """Test logging configuration with file handler."""
        configure_logging(level="INFO", log_file=temp_log_file)
        logger = get_logger("test")

        logger.info("Test message")

        assert temp_log_file.exists()
        assert "Test message" in temp_log_file.read_text()

    def test_configure_logging_idempotent(self):
        """Test that configure_logging is idempotent."""
        configure_logging(level="INFO")
        root = logging.getLogger()
        handler_count = len(root.handlers)

        # Call again - should not add more handlers
        configure_logging(level="DEBUG")
        assert len(root.handlers) == handler_count

    def test_configure_logging_debug_level(self):
        """Test debug level configuration."""
        configure_logging(level="DEBUG")
        root = logging.getLogger()

        assert root.level == logging.DEBUG

    def test_get_logger_returns_named_logger(self):
        """Test that get_logger returns properly named logger."""
        configure_logging(level="INFO")
        logger = get_logger("my.module.name")

        assert logger.name == "my.module.name"

    def test_reset_logging_clears_configuration(self):
        """Test that reset_logging clears all configuration."""
        configure_logging(level="INFO")
        root = logging.getLogger()
        assert len(root.handlers) > 0

        reset_logging()
        assert len(root.handlers) == 0


class TestConfigureLoggingWithLoki:
    """Tests for Loki integration in configure_logging."""

    def test_configure_logging_loki_disabled_by_default(self):
        """Test that Loki is disabled by default."""
        configure_logging(level="INFO")
        root = logging.getLogger()

        # Should not have LokiHandler
        from scruffy.frameworks_and_drivers.utils.loki_handler import LokiHandler

        loki_handlers = [h for h in root.handlers if isinstance(h, LokiHandler)]
        assert len(loki_handlers) == 0

    def test_configure_logging_loki_enabled(self):
        """Test that Loki handler is added when enabled."""
        configure_logging(
            level="INFO",
            loki_enabled=True,
            loki_url="http://localhost:3100/loki/api/v1/push",
            loki_labels={"app": "test"},
        )
        root = logging.getLogger()

        from scruffy.frameworks_and_drivers.utils.loki_handler import LokiHandler

        loki_handlers = [h for h in root.handlers if isinstance(h, LokiHandler)]
        assert len(loki_handlers) == 1
        assert loki_handlers[0].url == "http://localhost:3100/loki/api/v1/push"
        assert loki_handlers[0].labels == {"app": "test"}

    def test_configure_logging_loki_not_added_without_url(self):
        """Test that Loki handler is not added without URL."""
        configure_logging(level="INFO", loki_enabled=True, loki_url=None)
        root = logging.getLogger()

        from scruffy.frameworks_and_drivers.utils.loki_handler import LokiHandler

        loki_handlers = [h for h in root.handlers if isinstance(h, LokiHandler)]
        assert len(loki_handlers) == 0
