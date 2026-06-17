"""
Logging configuration module
"""

import logging
from logging.handlers import RotatingFileHandler

from config import LOG_PATH


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure application logging.
    """

    log_format = (
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )

    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        return

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return named logger for project modules.
    """

    return logging.getLogger(name)