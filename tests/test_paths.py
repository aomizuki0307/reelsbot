"""Tests for path utilities."""

import pytest
from pathlib import Path

from reelsbot.utils.paths import (
    ensure_dir,
    ensure_output_dir,
    get_temp_path,
    safe_filename,
    to_ffmpeg_path,
)


class TestPathUtilities:
    """Tests for path utility functions."""

    def test_to_ffmpeg_path_converts_backslashes(self) -> None:
        """Test that Windows backslashes are converted to forward slashes."""
        windows_path = Path("C:\\Users\\test\\video.mp4")
        ffmpeg_path = to_ffmpeg_path(windows_path)

        assert "/" in ffmpeg_path
        assert "\\" not in ffmpeg_path

    def test_to_ffmpeg_path_handles_spaces(self) -> None:
        """Test that paths with spaces are handled correctly."""
        path_with_spaces = Path("C:\\My Videos\\output file.mp4")
        ffmpeg_path = to_ffmpeg_path(path_with_spaces)

        # Should contain the space but use forward slashes
        assert "My Videos" in ffmpeg_path or "My%20Videos" in ffmpeg_path
        assert "\\" not in ffmpeg_path

    def test_to_ffmpeg_path_absolute(self) -> None:
        """Test that relative paths are converted to absolute."""
        relative_path = Path("video.mp4")
        ffmpeg_path = to_ffmpeg_path(relative_path)

        # Should be an absolute path
        assert Path(ffmpeg_path).is_absolute() or ffmpeg_path.startswith("/")

    def test_ensure_output_dir_creates_directory(self, tmp_path: Path) -> None:
        """Test that ensure_output_dir creates the directory."""
        run_id = "test_run_123"
        output_dir = ensure_output_dir(run_id, tmp_path)

        assert output_dir.exists()
        assert output_dir.is_dir()
        assert output_dir.name == run_id

    def test_ensure_output_dir_idempotent(self, tmp_path: Path) -> None:
        """Test that calling ensure_output_dir multiple times is safe."""
        run_id = "test_run_456"

        # Call twice
        output_dir1 = ensure_output_dir(run_id, tmp_path)
        output_dir2 = ensure_output_dir(run_id, tmp_path)

        # Should return the same path
        assert output_dir1 == output_dir2
        assert output_dir1.exists()

    def test_ensure_output_dir_default_base(self) -> None:
        """Test ensure_output_dir with default base directory."""
        run_id = "test_run_default"
        output_dir = ensure_output_dir(run_id)

        assert output_dir.exists()
        assert "outputs" in str(output_dir)
        assert output_dir.name == run_id

        # Cleanup
        output_dir.rmdir()

    def test_ensure_dir_creates_directory(self, tmp_path: Path) -> None:
        """Test that ensure_dir creates a directory."""
        test_dir = tmp_path / "test_directory"

        result = ensure_dir(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()
        assert result == test_dir

    def test_ensure_dir_creates_parents(self, tmp_path: Path) -> None:
        """Test that ensure_dir creates parent directories."""
        nested_dir = tmp_path / "parent" / "child" / "grandchild"

        ensure_dir(nested_dir)

        assert nested_dir.exists()
        assert (tmp_path / "parent").exists()
        assert (tmp_path / "parent" / "child").exists()

    def test_safe_filename_removes_invalid_chars(self) -> None:
        """Test that safe_filename removes invalid Windows characters."""
        unsafe_name = 'test<>:"/\\|?*file.txt'
        safe_name = safe_filename(unsafe_name)

        # Check invalid characters are removed
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            assert char not in safe_name

    def test_safe_filename_preserves_valid_chars(self) -> None:
        """Test that safe_filename preserves valid characters."""
        filename = "My_Video-Part_1_(2025).mp4"
        safe_name = safe_filename(filename)

        # Should preserve underscores, hyphens, parentheses, dots
        assert "_" in safe_name or " " in safe_name
        assert "-" in safe_name or " " in safe_name
        assert "2025" in safe_name

    def test_safe_filename_handles_multiple_spaces(self) -> None:
        """Test that multiple consecutive spaces are collapsed."""
        filename = "test    multiple     spaces.txt"
        safe_name = safe_filename(filename)

        # Should not have multiple consecutive spaces
        assert "  " not in safe_name

    def test_safe_filename_respects_max_length(self) -> None:
        """Test that safe_filename respects maximum length."""
        long_filename = "A" * 300
        safe_name = safe_filename(long_filename, max_length=50)

        assert len(safe_name) <= 50

    def test_safe_filename_default_max_length(self) -> None:
        """Test safe_filename with default max length."""
        long_filename = "B" * 300
        safe_name = safe_filename(long_filename)

        assert len(safe_name) <= 200

    def test_get_temp_path_creates_path(self, tmp_path: Path) -> None:
        """Test that get_temp_path creates a valid temporary path."""
        run_id = "test_run_789"
        temp_path = get_temp_path(tmp_path, run_id, ".mp4")

        # Check path structure
        assert temp_path.parent == tmp_path / run_id
        assert temp_path.name == "temp.mp4"
        assert temp_path.suffix == ".mp4"

    def test_get_temp_path_creates_run_dir(self, tmp_path: Path) -> None:
        """Test that get_temp_path creates the run directory."""
        run_id = "test_run_temp"
        temp_path = get_temp_path(tmp_path, run_id, ".tmp")

        # Run directory should exist
        run_dir = tmp_path / run_id
        assert run_dir.exists()
        assert run_dir.is_dir()

    def test_get_temp_path_default_suffix(self, tmp_path: Path) -> None:
        """Test get_temp_path with default suffix."""
        run_id = "test_run_suffix"
        temp_path = get_temp_path(tmp_path, run_id)

        assert temp_path.suffix == ".tmp"
        assert temp_path.name == "temp.tmp"
