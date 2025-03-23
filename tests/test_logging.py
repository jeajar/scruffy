import logging
import logging.handlers

import pytest

from scruffy.logging import setup_logger


@pytest.fixture(autouse=True)
def cleanup_logging():
    yield
    # Clear all handlers after each test
    root = logging.getLogger()
    root.handlers.clear()
    # Clear any loggers created during tests
    logging.Logger.manager.loggerDict.clear()


@pytest.fixture
def temp_log_file(tmp_path):
    return tmp_path / "test.log"


def test_setup_logger_basic():
    logger = setup_logger("test")

    assert logger.name == "test"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 0


def test_setup_logger_with_file(temp_log_file):
    logger = setup_logger("test", log_file=temp_log_file)

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.handlers.RotatingFileHandler)
    assert logger.handlers[0].baseFilename == str(temp_log_file)
    assert logger.handlers[0].maxBytes == 10_000_000
    assert logger.handlers[0].backupCount == 5


def test_setup_logger_custom_level():
    logger = setup_logger("test", level="DEBUG")
    assert logger.level == logging.DEBUG


def test_logger_writes_to_file(temp_log_file):
    logger = setup_logger("test", log_file=temp_log_file)
    test_message = "Test log message"

    logger.info(test_message)

    assert temp_log_file.exists()
    log_content = temp_log_file.read_text()
    assert test_message in log_content


def test_logger_rotating_file(temp_log_file):
    logger = setup_logger("test", log_file=temp_log_file)
    handler = logger.handlers[0]

    assert isinstance(handler, logging.handlers.RotatingFileHandler)
    assert handler.maxBytes == 10_000_000
    assert handler.backupCount == 5


def test_setup_logger_invalid_level():
    with pytest.raises(ValueError):
        setup_logger("test", level="INVALID")
