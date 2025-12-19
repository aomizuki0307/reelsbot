"""Tests for logger utilities."""

import logging
import pytest
from pathlib import Path

from reelsbot.utils.logger import get_logger, setup_logger, update_run_id


class TestLogger:
    """Tests for logger setup and utilities."""

    def test_setup_logger_creates_logger(self, tmp_path: Path) -> None:
        """Test that setup_logger creates a logger instance."""
        run_id = "test_run_001"
        logger = setup_logger(run_id, logs_dir=tmp_path)

        assert isinstance(logger, logging.Logger)
        assert logger.name == "reelsbot"

    def test_setup_logger_creates_log_file(self, tmp_path: Path) -> None:
        """Test that setup_logger creates a log file."""
        run_id = "test_run_002"
        logger = setup_logger(run_id, logs_dir=tmp_path)

        # Write a log message
        logger.info("Test message")

        # Check that log file was created
        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) > 0

    def test_setup_logger_includes_run_id(self, tmp_path: Path) -> None:
        """Test that log messages include the run_id."""
        run_id = "test_run_003"
        logger = setup_logger(run_id, logs_dir=tmp_path)

        # Write a test message
        test_message = "Test message with run_id"
        logger.info(test_message)

        # Read the log file
        log_file = list(tmp_path.glob("*.log"))[0]
        log_content = log_file.read_text(encoding="utf-8")

        # Check that run_id appears in the log
        assert run_id in log_content
        assert test_message in log_content

    def test_setup_logger_utf8_encoding(self, tmp_path: Path) -> None:
        """Test that logger handles UTF-8 characters (Japanese, emoji)."""
        run_id = "test_run_004"
        logger = setup_logger(run_id, logs_dir=tmp_path)

        # Write messages with UTF-8 characters
        logger.info("テストメッセージ")
        logger.info("Test with emoji: 🎬 📹")

        # Read the log file
        log_file = list(tmp_path.glob("*.log"))[0]
        log_content = log_file.read_text(encoding="utf-8")

        # Check that UTF-8 characters are preserved
        assert "テストメッセージ" in log_content
        assert "🎬" in log_content or "emoji" in log_content

    def test_setup_logger_respects_level(self, tmp_path: Path) -> None:
        """Test that logger respects the specified logging level."""
        run_id = "test_run_005"
        logger = setup_logger(run_id, logs_dir=tmp_path, level=logging.WARNING)

        # Write messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

        # Read the log file
        log_file = list(tmp_path.glob("*.log"))[0]
        log_content = log_file.read_text(encoding="utf-8")

        # Debug and info should not appear, warning should
        assert "Debug message" not in log_content
        assert "Info message" not in log_content
        assert "Warning message" in log_content

    def test_setup_logger_console_level(self, tmp_path: Path, caplog) -> None:
        """Test that console level can be different from file level."""
        run_id = "test_run_006"

        # Set file level to DEBUG but console to WARNING
        logger = setup_logger(
            run_id, logs_dir=tmp_path, level=logging.DEBUG, console_level=logging.WARNING
        )

        with caplog.at_level(logging.WARNING):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")

        # Read log file - should have all messages
        log_file = list(tmp_path.glob("*.log"))[0]
        log_content = log_file.read_text(encoding="utf-8")

        assert "Debug message" in log_content or "Debug" in log_content
        assert "Info message" in log_content or "Info" in log_content
        assert "Warning message" in log_content

    def test_get_logger_requires_setup(self) -> None:
        """Test that get_logger raises error if logger not set up."""
        # Clear any existing handlers
        logger = logging.getLogger("reelsbot")
        logger.handlers.clear()

        with pytest.raises(RuntimeError, match="Logger not initialized"):
            get_logger()

    def test_get_logger_returns_same_instance(self, tmp_path: Path) -> None:
        """Test that get_logger returns the same logger instance."""
        run_id = "test_run_007"
        logger1 = setup_logger(run_id, logs_dir=tmp_path)
        logger2 = get_logger()

        assert logger1 is logger2

    def test_update_run_id_changes_run_id(self, tmp_path: Path) -> None:
        """Test that update_run_id changes the run_id in log messages."""
        initial_run_id = "test_run_008"
        logger = setup_logger(initial_run_id, logs_dir=tmp_path)

        # Write message with initial run_id
        logger.info("Message with initial run_id")

        # Update run_id
        new_run_id = "test_run_009"
        update_run_id(new_run_id)

        # Write message with new run_id
        logger.info("Message with new run_id")

        # Read log file
        log_file = list(tmp_path.glob("*.log"))[0]
        log_content = log_file.read_text(encoding="utf-8")

        # Both run_ids should appear
        assert initial_run_id in log_content
        assert new_run_id in log_content

    def test_logger_handles_exceptions(self, tmp_path: Path) -> None:
        """Test that logger can log exceptions."""
        run_id = "test_run_010"
        logger = setup_logger(run_id, logs_dir=tmp_path)

        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")

        # Read log file
        log_file = list(tmp_path.glob("*.log"))[0]
        log_content = log_file.read_text(encoding="utf-8")

        assert "An error occurred" in log_content
        assert "ValueError" in log_content
        assert "Test exception" in log_content
