"""Unit tests for FFmpeg utility functions."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reelsbot.utils.ffmpeg import (
    build_filter_complex,
    check_ffmpeg_available,
    convert_to_h264,
    get_video_info,
    run_ffmpeg_command,
)
from reelsbot.utils.logger import setup_logger


@pytest.fixture
def logger():
    """Provide a test logger."""
    return setup_logger("test_ffmpeg")


class TestCheckFFmpegAvailable:
    """Test FFmpeg availability check."""

    @patch("subprocess.run")
    def test_ffmpeg_available(self, mock_run):
        """Test when FFmpeg is available."""
        mock_run.return_value = MagicMock(returncode=0)
        assert check_ffmpeg_available() is True

    @patch("subprocess.run")
    def test_ffmpeg_not_available(self, mock_run):
        """Test when FFmpeg is not available."""
        mock_run.return_value = MagicMock(returncode=1)
        assert check_ffmpeg_available() is False

    @patch("subprocess.run")
    def test_ffmpeg_not_found(self, mock_run):
        """Test when FFmpeg is not in PATH."""
        mock_run.side_effect = FileNotFoundError()
        assert check_ffmpeg_available() is False

    @patch("subprocess.run")
    def test_ffmpeg_timeout(self, mock_run):
        """Test when FFmpeg check times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 5)
        assert check_ffmpeg_available() is False


class TestRunFFmpegCommand:
    """Test FFmpeg command execution."""

    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_ffmpeg_not_available(self, mock_check, logger):
        """Test error when FFmpeg not available."""
        mock_check.return_value = False

        with pytest.raises(RuntimeError, match="FFmpeg is not available"):
            run_ffmpeg_command(["ffmpeg", "-version"], logger)

    @patch("subprocess.run")
    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_successful_command(self, mock_check, mock_run, logger):
        """Test successful FFmpeg command execution."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="FFmpeg output",
            stderr="",
        )

        result = run_ffmpeg_command(["ffmpeg", "-version"], logger)

        assert result.returncode == 0
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_failed_command(self, mock_check, mock_run, logger):
        """Test failed FFmpeg command execution."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: invalid option",
        )

        with pytest.raises(RuntimeError, match="FFmpeg command failed"):
            run_ffmpeg_command(["ffmpeg", "-invalid"], logger)

    @patch("subprocess.run")
    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_timeout(self, mock_check, mock_run, logger):
        """Test command timeout."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 300)

        with pytest.raises(subprocess.TimeoutExpired):
            run_ffmpeg_command(["ffmpeg", "-i", "long_video.mp4"], logger)

    @patch("subprocess.run")
    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_custom_timeout(self, mock_check, mock_run, logger):
        """Test custom timeout parameter."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        run_ffmpeg_command(["ffmpeg", "-version"], logger, timeout=60)

        # Check timeout was passed to subprocess.run
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 60


class TestBuildFilterComplex:
    """Test filter_complex string builder."""

    def test_empty_filters(self):
        """Test with empty filter list."""
        result = build_filter_complex([])
        assert result == ""

    def test_single_filter(self):
        """Test with single filter."""
        filters = ["scale=1920:1080"]
        result = build_filter_complex(filters)
        assert result == "scale=1920:1080"

    def test_multiple_filters(self):
        """Test with multiple filters."""
        filters = [
            "scale=1920:1080",
            "drawtext=text='Hello':x=100:y=100",
            "fade=in:0:30",
        ]
        result = build_filter_complex(filters)
        expected = "scale=1920:1080,drawtext=text='Hello':x=100:y=100,fade=in:0:30"
        assert result == expected


class TestGetVideoInfo:
    """Test video information extraction."""

    @patch("subprocess.run")
    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_get_video_info_success(self, mock_check, mock_run, logger, tmp_path):
        """Test successful video info extraction."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="duration=10.5\nwidth=1920\nheight=1080\ncodec_name=h264\n",
            stderr="",
        )

        video_path = tmp_path / "test.mp4"
        video_path.touch()

        info = get_video_info(video_path, logger)

        assert info["duration"] == "10.5"
        assert info["width"] == "1920"
        assert info["height"] == "1080"
        assert info["codec_name"] == "h264"

    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_get_video_info_ffmpeg_not_available(self, mock_check, logger, tmp_path):
        """Test error when FFmpeg not available."""
        mock_check.return_value = False

        video_path = tmp_path / "test.mp4"

        with pytest.raises(RuntimeError, match="FFprobe is not available"):
            get_video_info(video_path, logger)

    @patch("subprocess.run")
    @patch("reelsbot.utils.ffmpeg.check_ffmpeg_available")
    def test_get_video_info_failed(self, mock_check, mock_run, logger, tmp_path):
        """Test failed video info extraction."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: file not found",
        )

        video_path = tmp_path / "missing.mp4"

        with pytest.raises(RuntimeError, match="ffprobe failed"):
            get_video_info(video_path, logger)


class TestConvertToH264:
    """Test H.264 video conversion."""

    @patch("reelsbot.utils.ffmpeg.run_ffmpeg_command")
    def test_convert_to_h264(self, mock_run, logger, tmp_path):
        """Test successful H.264 conversion."""
        input_path = tmp_path / "input.mov"
        output_path = tmp_path / "output.mp4"
        input_path.touch()

        result = convert_to_h264(input_path, output_path, logger)

        assert result == output_path
        mock_run.assert_called_once()

        # Check command structure
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd
        assert "-vcodec" in cmd
        assert "libx264" in cmd

    @patch("reelsbot.utils.ffmpeg.run_ffmpeg_command")
    def test_convert_to_h264_custom_params(self, mock_run, logger, tmp_path):
        """Test H.264 conversion with custom parameters."""
        input_path = tmp_path / "input.mov"
        output_path = tmp_path / "output.mp4"
        input_path.touch()

        result = convert_to_h264(
            input_path, output_path, logger, crf=20, preset="slow"
        )

        assert result == output_path

        # Check CRF and preset in command
        cmd = mock_run.call_args[0][0]
        assert "-crf" in cmd
        assert "20" in cmd
        assert "-preset" in cmd
        assert "slow" in cmd
