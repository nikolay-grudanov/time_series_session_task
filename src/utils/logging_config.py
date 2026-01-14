"""
Standard Python logging configuration with rotation strategy.
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging_with_rotation(
    log_file: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    level: int = logging.INFO
) -> None:
    """
    Sets up logging with rotation strategy.
    Creates logs directory if it doesn't exist.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create rotating file handler
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Also add console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
