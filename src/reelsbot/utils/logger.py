"""Logging utilities for reelsbot with run-ID-based tracking.

This module provides a standardized logging setup with run ID tracking,
file and console output, and UTF-8 encoding for international character support.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class RunIDFormatter(logging.Formatter):
    """Custom formatter that includes run_id in all log messages.

    The run_id is stored as a class variable so all loggers can access it.
    """

    run_id: str = "unknown"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with run_id included.

        Args:
            record: Log record to format.

        Returns:
            Formatted log message string.
        """
        # Add run_id to the record
        record.run_id = self.run_id
        return super().format(record)


def setup_logger(
    run_id: str,
    logs_dir: Path = Path("logs"),
    level: int = logging.INFO,
    console_level: Optional[int] = None,
) -> logging.Logger:
    """Set up logger with run-ID-based tracking and dual output.

    Creates a logger that writes to both a date-based log file and console.
    All log messages include the run_id for tracking execution flows.

    Args:
        run_id: Unique identifier for this execution run.
        logs_dir: Directory to store log files (default: "logs").
        level: Logging level for file output (default: INFO).
        console_level: Logging level for console output (default: same as level).

    Returns:
        Configured logger instance.

    Example:
        >>> logger = setup_logger("run_20250101_123456")
        >>> logger.info("Processing started")
        2025-01-01 12:34:56 [run_20250101_123456] INFO: Processing started
    """
    # Set the run_id in the formatter class
    RunIDFormatter.run_id = run_id

    # Create logger
    logger = logging.getLogger("reelsbot")
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console level defaults to file level if not specified
    if console_level is None:
        console_level = level

    # Create formatters
    detailed_formatter = RunIDFormatter(
        fmt="%(asctime)s [%(run_id)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = RunIDFormatter(
        fmt="[%(run_id)s] %(levelname)s: %(message)s",
    )

    # File handler - date-based filename
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_filename = f"{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = logs_dir / log_filename

    file_handler = logging.FileHandler(
        log_filepath,
        mode="a",
        encoding="utf-8",  # UTF-8 for Japanese/emoji support
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log initial message
    logger.info(f"Logger initialized for run_id: {run_id}")
    logger.debug(f"Log file: {log_filepath.absolute()}")

    return logger


def get_logger() -> logging.Logger:
    """Get the reelsbot logger instance.

    Returns:
        Logger instance (must be initialized with setup_logger first).

    Raises:
        RuntimeError: If logger has not been set up yet.
    """
    logger = logging.getLogger("reelsbot")
    if not logger.handlers:
        raise RuntimeError(
            "Logger not initialized. Call setup_logger() first before using get_logger()."
        )
    return logger


def update_run_id(run_id: str) -> None:
    """Update the run_id for all subsequent log messages.

    This can be useful if you need to change the run_id mid-execution,
    though typically you should create a new logger instead.

    Args:
        run_id: New run identifier to use.
    """
    RunIDFormatter.run_id = run_id
    logger = logging.getLogger("reelsbot")
    if logger.handlers:
        logger.info(f"Run ID updated to: {run_id}")
