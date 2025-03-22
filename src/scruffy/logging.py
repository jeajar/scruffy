import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Path | None = None,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """
    Configure and return a logger instance using Rich for console logging.
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
