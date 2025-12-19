"""FFmpeg wrapper utilities for video generation and editing.

This module provides helper functions for executing FFmpeg commands with
proper error handling, logging, and Windows path compatibility.
"""

import logging
import subprocess
from pathlib import Path

from reelsbot.utils.paths import to_ffmpeg_path


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in the system PATH.

    Returns:
        True if ffmpeg is available, False otherwise.

    Example:
        >>> if check_ffmpeg_available():
        ...     print("FFmpeg is ready")
        ... else:
        ...     print("FFmpeg not found")
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def run_ffmpeg_command(
    cmd: list[str],
    logger: logging.Logger,
    timeout: int = 300,
) -> subprocess.CompletedProcess:
    """Execute an FFmpeg command with logging and error handling.

    Args:
        cmd: FFmpeg command as a list of arguments (e.g., ["ffmpeg", "-i", "input.mp4"]).
        logger: Logger instance for command logging.
        timeout: Command timeout in seconds (default: 300).

    Returns:
        CompletedProcess instance with command results.

    Raises:
        RuntimeError: If FFmpeg is not available or command fails.
        subprocess.TimeoutExpired: If command exceeds timeout.

    Example:
        >>> cmd = ["ffmpeg", "-i", "input.mp4", "-vf", "scale=1920:1080", "output.mp4"]
        >>> result = run_ffmpeg_command(cmd, logger)
        >>> print(f"Exit code: {result.returncode}")
    """
    # Check FFmpeg availability
    if not check_ffmpeg_available():
        raise RuntimeError(
            "FFmpeg is not available. Please install FFmpeg and add it to PATH. "
            "Download from: https://ffmpeg.org/download.html"
        )

    # Log command (truncate very long commands)
    cmd_str = " ".join(cmd)
    if len(cmd_str) > 500:
        cmd_str = cmd_str[:500] + "..."
    logger.debug(f"Executing FFmpeg command: {cmd_str}")

    try:
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"FFmpeg command failed with exit code {result.returncode}")
            logger.error(f"Error output: {error_msg}")
            raise RuntimeError(
                f"FFmpeg command failed (exit code {result.returncode}): {error_msg}"
            )

        # Log success
        logger.debug(f"FFmpeg command completed successfully")
        if result.stdout:
            logger.debug(f"Output: {result.stdout[:200]}")

        return result

    except subprocess.TimeoutExpired as e:
        logger.error(f"FFmpeg command timed out after {timeout} seconds")
        raise
    except subprocess.SubprocessError as e:
        logger.error(f"FFmpeg subprocess error: {e}")
        raise RuntimeError(f"FFmpeg execution error: {e}") from e


def build_filter_complex(filters: list[str]) -> str:
    """Construct a filter_complex string from a list of filter expressions.

    Args:
        filters: List of filter expressions to combine.

    Returns:
        Combined filter_complex string with filters separated by commas.

    Example:
        >>> filters = [
        ...     "scale=1080:1920",
        ...     "drawtext=text='Hello':fontsize=48:x=100:y=100"
        ... ]
        >>> complex_str = build_filter_complex(filters)
        >>> print(complex_str)
        scale=1080:1920,drawtext=text='Hello':fontsize=48:x=100:y=100
    """
    return ",".join(filters)


def get_video_info(video_path: Path, logger: logging.Logger) -> dict[str, str]:
    """Get basic information about a video file using ffprobe.

    Args:
        video_path: Path to the video file.
        logger: Logger instance.

    Returns:
        Dictionary with video metadata (duration, resolution, codec, etc.).

    Raises:
        RuntimeError: If ffprobe is not available or command fails.

    Example:
        >>> info = get_video_info(Path("video.mp4"), logger)
        >>> print(f"Duration: {info.get('duration')}")
    """
    # Check FFmpeg availability (ffprobe comes with FFmpeg)
    if not check_ffmpeg_available():
        raise RuntimeError("FFprobe is not available. Please install FFmpeg.")

    ffmpeg_path = to_ffmpeg_path(video_path)

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration:stream=width,height,codec_name",
        "-of", "default=noprint_wrappers=1",
        ffmpeg_path,
    ]

    logger.debug(f"Getting video info: {video_path}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"ffprobe failed: {error_msg}")

        # Parse output
        info = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                info[key.strip()] = value.strip()

        return info

    except subprocess.TimeoutExpired:
        raise RuntimeError("ffprobe timed out")
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"ffprobe error: {e}") from e


def convert_to_h264(
    input_path: Path,
    output_path: Path,
    logger: logging.Logger,
    crf: int = 23,
    preset: str = "medium",
) -> Path:
    """Convert a video to H.264 format with specified quality settings.

    Args:
        input_path: Source video file.
        output_path: Destination video file.
        logger: Logger instance.
        crf: Constant Rate Factor (0-51, lower = better quality, default: 23).
        preset: Encoding preset (ultrafast, fast, medium, slow, veryslow).

    Returns:
        Path to the output file.

    Raises:
        RuntimeError: If conversion fails.

    Example:
        >>> output = convert_to_h264(
        ...     Path("input.mov"),
        ...     Path("output.mp4"),
        ...     logger,
        ...     crf=20,
        ...     preset="slow"
        ... )
    """
    input_ffmpeg = to_ffmpeg_path(input_path)
    output_ffmpeg = to_ffmpeg_path(output_path)

    cmd = [
        "ffmpeg",
        "-i", input_ffmpeg,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", str(crf),
        "-preset", preset,
        "-an",  # No audio
        "-y",  # Overwrite output
        output_ffmpeg,
    ]

    run_ffmpeg_command(cmd, logger)
    return output_path
