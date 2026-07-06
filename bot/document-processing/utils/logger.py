"""Logging configuration for document processing."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structured console logging once for the process."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s %(levelname)s %(name)s "
            "%(message)s file_path=%(file_path)s "
            "duration_seconds=%(duration_seconds)s error=%(error)s"
        )
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


class ContextDefaultsFilter(logging.Filter):
    """Add default structured fields expected by the formatter."""

    def filter(self, record: logging.LogRecord) -> bool:
        for field in ("file_path", "duration_seconds", "error"):
            if not hasattr(record, field):
                setattr(record, field, "")
        return True


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with default structured fields."""
    configure_logging()
    logger = logging.getLogger(name)
    if not any(isinstance(item, ContextDefaultsFilter) for item in logger.filters):
        logger.addFilter(ContextDefaultsFilter())
    return logger
