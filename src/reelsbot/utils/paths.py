"""Path utilities for Windows-safe file handling and ffmpeg compatibility.

This module provides utilities for handling paths on Windows, converting them
to ffmpeg-compatible formats, and managing output directories.
"""

from pathlib import Path


def to_ffmpeg_path(path: Path) -> str:
    """Convert Windows path to ffmpeg-compatible format.

    FFmpeg on Windows prefers forward slashes and can have issues with backslashes.
    This function converts Windows paths to use forward slashes and handles spaces correctly.

    Args:
        path: Path object to convert.

    Returns:
        String path with forward slashes suitable for ffmpeg.

    Examples:
        >>> to_ffmpeg_path(Path("C:\\Users\\name\\video.mp4"))
        'C:/Users/name/video.mp4'
        >>> to_ffmpeg_path(Path("C:\\My Videos\\output.mp4"))
        'C:/My Videos/output.mp4'
    """
    # Convert to absolute path first
    abs_path = path.resolve()

    # Convert backslashes to forward slashes
    # as_posix() returns the path with forward slashes
    return abs_path.as_posix()


def ensure_output_dir(run_id: str, base_dir: Path = Path("outputs")) -> Path:
    """Create and return output directory for a specific run.

    Creates a directory structure: base_dir/run_id/
    The directory is created if it doesn't exist.

    Args:
        run_id: Unique identifier for this run.
        base_dir: Base directory for outputs (default: "outputs").

    Returns:
        Path object for the run's output directory.

    Examples:
        >>> output_dir = ensure_output_dir("run_20250101_123456")
        >>> print(output_dir)
        outputs/run_20250101_123456
    """
    output_path = base_dir / run_id

    # Create directory and any necessary parent directories
    output_path.mkdir(parents=True, exist_ok=True)

    return output_path


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path object (for chaining).

    Examples:
        >>> data_dir = ensure_dir(Path("data/videos"))
        >>> assert data_dir.exists()
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str, max_length: int = 200) -> str:
    """Convert string to safe filename by removing/replacing invalid characters.

    Removes or replaces characters that are invalid in Windows filenames:
    < > : " / \\ | ? *

    Also handles spaces and limits the length to avoid path length issues.

    Args:
        filename: Original filename string.
        max_length: Maximum length for the filename (default: 200).

    Returns:
        Safe filename string.

    Examples:
        >>> safe_filename("My Video: Part 1 (2025)")
        'My Video Part 1 (2025)'
        >>> safe_filename('Invalid <chars> here?')
        'Invalid chars here'
    """
    # Characters that are invalid in Windows filenames
    invalid_chars = '<>:"/\\|?*'

    # Replace invalid characters with empty string
    safe_name = filename
    for char in invalid_chars:
        safe_name = safe_name.replace(char, "")

    # Replace multiple spaces with single space
    safe_name = " ".join(safe_name.split())

    # Trim to max length
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip()

    return safe_name


def get_temp_path(base_dir: Path, run_id: str, suffix: str = ".tmp") -> Path:
    """Generate a temporary file path within the run's output directory.

    Args:
        base_dir: Base output directory.
        run_id: Run identifier.
        suffix: File suffix/extension (default: ".tmp").

    Returns:
        Path for temporary file.

    Examples:
        >>> temp_path = get_temp_path(Path("outputs"), "run_123", ".mp4")
        >>> print(temp_path)
        outputs/run_123/temp.mp4
    """
    run_dir = ensure_output_dir(run_id, base_dir)
    return run_dir / f"temp{suffix}"
