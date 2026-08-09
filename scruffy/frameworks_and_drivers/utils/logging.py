"""Logging configuration and utilities for Scruffy."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

from scruffy.frameworks_and_drivers.utils.loki_handler import JsonFormatter, LokiHandler

# Track if logging has been configured globally
_logging_configured = False

# Default format for human-readable logs
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class ExtraFieldsFormatter(logging.Formatter):
    """Formatter that appends logger.*(..., extra={...}) fields to the message.

    Without this, RichHandler/logging.Formatter render only %(message)s and
    silently drop everything passed via `extra=`, which is how call sites
    throughout this codebase attach the actual error/context (e.g. the
    underlying connection error behind "Failed to fetch media list").
    """

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in JsonFormatter.RESERVED_ATTRS and not key.startswith("_")
        }
        if extras:
            extras_str = " ".join(f"{key}={value!r}" for key, value in extras.items())
            message = f"{message} ({extras_str})"
        return message


def configure_logging(
    level: str = "INFO",
    log_file: str | Path | None = None,
    loki_enabled: bool = False,
    loki_url: str | None = None,
    loki_labels: dict[str, str] | None = None,
) -> None:
    """
    Configure the root logger with appropriate handlers.

    This should be called once at application startup. Subsequent calls
    will be ignored to prevent duplicate handlers.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to a log file for rotating file handler
        loki_enabled: Whether to enable Loki log shipping
        loki_url: Loki push API URL (required if loki_enabled is True)
        loki_labels: Static labels to attach to Loki log streams
    """
    global _logging_configured

    if _logging_configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler with Rich for colorful, human-readable output
    console_handler = RichHandler(
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
    )
    console_handler.setFormatter(ExtraFieldsFormatter("%(message)s"))
    console_handler.setLevel(level.upper())
    root_logger.addHandler(console_handler)

    # Optional file handler with rotation
    if log_file:
        file_path = Path(log_file) if isinstance(log_file, str) else log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
        )
        file_handler.setFormatter(ExtraFieldsFormatter(DEFAULT_FORMAT))
        file_handler.setLevel(level.upper())
        root_logger.addHandler(file_handler)

    # Optional Loki handler for centralized logging
    if loki_enabled and loki_url:
        loki_handler = LokiHandler(
            url=loki_url,
            labels=loki_labels or {"app": "scruffy"},
        )
        loki_handler.setLevel(level.upper())
        root_logger.addHandler(loki_handler)

    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    This is the preferred way to get loggers throughout the application.
    The logger will inherit configuration from the root logger set up
    by configure_logging().

    Args:
        name: Logger name, typically __name__ of the calling module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Path | None = None,
    format_string: str = DEFAULT_FORMAT,
) -> logging.Logger:
    """
    Configure and return a logger instance using Rich for console logging.

    DEPRECATED: Use configure_logging() at startup and get_logger() to
    obtain logger instances instead.

    Args:
        name: Logger name
        level: Log level string
        log_file: Optional path to log file
        format_string: Format string for log messages

    Returns:
        Configured logger instance
    """
    # Setup basic configuration with RichHandler for colorful console output.
    logging.basicConfig(
        level=level.upper(),
        format=format_string,
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    # Optionally add a file handler if a log_file is provided.
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
        )
        formatter = logging.Formatter(format_string)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def reset_logging() -> None:
    """
    Reset logging configuration. Primarily for testing purposes.
    """
    global _logging_configured
    _logging_configured = False
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    logging.Logger.manager.loggerDict.clear()
