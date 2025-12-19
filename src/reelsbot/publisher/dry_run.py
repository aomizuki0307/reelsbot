"""DRY_RUN publisher implementation for local file storage.

This publisher saves generated Reels to local disk instead of publishing
to Instagram, useful for testing and preview purposes.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from reelsbot.config import ReelsbotConfig
from reelsbot.models import ReelMetadata
from reelsbot.publisher.base import BasePublisher, PublisherError


class DryRunPublisher(BasePublisher):
    """Local file storage publisher for testing.

    Instead of publishing to Instagram, this publisher saves all content
    to a local directory structure for review and testing.

    Attributes:
        config: Reelsbot configuration instance.
        logger: Logger instance for tracking operations.
        output_base: Base directory for DRY_RUN outputs.
    """

    def __init__(
        self,
        config: ReelsbotConfig,
        logger: logging.Logger,
    ) -> None:
        """Initialize the DRY_RUN publisher.

        Args:
            config: Reelsbot configuration.
            logger: Logger instance.
        """
        self.config = config
        self.logger = logger

        # Create base output directory
        self.output_base = config.outputs_dir / "dry_run"
        self.output_base.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"DRY_RUN publisher initialized: {self.output_base}")

    async def publish(self, metadata: ReelMetadata) -> dict[str, Any]:
        """Save Reel to local directory.

        Creates a directory for the run and copies all files with metadata.

        Args:
            metadata: Complete Reel metadata.

        Returns:
            Dictionary with publication result:
                - status: "DRY_RUN"
                - output_dir: Path to output directory
                - files: Dictionary of copied file paths

        Raises:
            PublisherError: If file operations fail.
        """
        # Validate metadata first
        self.validate_metadata(metadata)

        try:
            # Create run directory
            run_dir = self.output_base / metadata.run_id
            run_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Publishing to DRY_RUN: {run_dir}")

            # Copy video file
            video_dest = run_dir / "video.mp4"
            shutil.copy2(metadata.video_path, video_dest)
            self.logger.debug(f"Copied video: {video_dest}")

            # Copy thumbnail if exists
            thumbnail_dest = None
            if metadata.thumbnail_path and metadata.thumbnail_path.exists():
                thumbnail_dest = run_dir / "thumbnail.jpg"
                shutil.copy2(metadata.thumbnail_path, thumbnail_dest)
                self.logger.debug(f"Copied thumbnail: {thumbnail_dest}")

            # Save metadata JSON
            metadata_dest = run_dir / "metadata.json"
            self._save_metadata_json(metadata, metadata_dest)
            self.logger.debug(f"Saved metadata: {metadata_dest}")

            # Save caption to text file
            caption_dest = run_dir / "caption.txt"
            self._save_caption_file(metadata, caption_dest)
            self.logger.debug(f"Saved caption: {caption_dest}")

            # Create result
            result = {
                "status": "DRY_RUN",
                "output_dir": str(run_dir),
                "files": {
                    "video": str(video_dest),
                    "thumbnail": str(thumbnail_dest) if thumbnail_dest else None,
                    "metadata": str(metadata_dest),
                    "caption": str(caption_dest),
                },
            }

            self.logger.info(
                f"DRY_RUN publish complete: {metadata.run_id} -> {run_dir}"
            )

            return result

        except Exception as e:
            raise PublisherError(
                f"Failed to publish to DRY_RUN: {e}"
            ) from e

    def get_status(self, run_id: str) -> dict[str, Any]:
        """Check if DRY_RUN output exists.

        Args:
            run_id: Unique identifier for the Reel run.

        Returns:
            Dictionary with status information:
                - status: "exists" or "not_found"
                - output_dir: Path to output directory (if exists)
                - files: Dictionary of file paths and existence status

        Examples:
            >>> status = publisher.get_status(run_id)
            >>> if status["status"] == "exists":
            ...     print(f"Output at: {status['output_dir']}")
        """
        run_dir = self.output_base / run_id

        if not run_dir.exists():
            return {
                "status": "not_found",
                "output_dir": str(run_dir),
            }

        # Check for expected files
        video_path = run_dir / "video.mp4"
        thumbnail_path = run_dir / "thumbnail.jpg"
        metadata_path = run_dir / "metadata.json"
        caption_path = run_dir / "caption.txt"

        return {
            "status": "exists",
            "output_dir": str(run_dir),
            "files": {
                "video": {
                    "path": str(video_path),
                    "exists": video_path.exists(),
                    "size": video_path.stat().st_size if video_path.exists() else 0,
                },
                "thumbnail": {
                    "path": str(thumbnail_path),
                    "exists": thumbnail_path.exists(),
                    "size": (
                        thumbnail_path.stat().st_size
                        if thumbnail_path.exists()
                        else 0
                    ),
                },
                "metadata": {
                    "path": str(metadata_path),
                    "exists": metadata_path.exists(),
                },
                "caption": {
                    "path": str(caption_path),
                    "exists": caption_path.exists(),
                },
            },
        }

    def _save_metadata_json(self, metadata: ReelMetadata, dest: Path) -> None:
        """Save metadata as JSON file.

        Args:
            metadata: Metadata to save.
            dest: Destination file path.
        """
        # Convert to dict and format nicely
        metadata_dict = json.loads(metadata.model_dump_json())

        with dest.open("w", encoding="utf-8") as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

    def _save_caption_file(self, metadata: ReelMetadata, dest: Path) -> None:
        """Save caption with hashtags to text file.

        Args:
            metadata: Metadata containing caption and hashtags.
            dest: Destination file path.
        """
        content_lines = [
            f"Run ID: {metadata.run_id}",
            f"Type: {metadata.plan.type}",
            f"Title: {metadata.plan.get_display_title()}",
            "",
            "CAPTION:",
            metadata.caption,
            "",
            "HASHTAGS:",
            metadata.get_hashtags_string(),
            "",
            "FULL CAPTION:",
            metadata.get_full_caption(),
        ]

        content = "\n".join(content_lines)

        with dest.open("w", encoding="utf-8") as f:
            f.write(content)

    def list_runs(self, limit: int | None = None) -> list[dict[str, Any]]:
        """List all DRY_RUN outputs.

        Args:
            limit: Maximum number of runs to return (None for all).

        Returns:
            List of dictionaries with run information.
        """
        runs = []

        if not self.output_base.exists():
            return runs

        # Get all run directories
        run_dirs = sorted(
            [d for d in self.output_base.iterdir() if d.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if limit:
            run_dirs = run_dirs[:limit]

        for run_dir in run_dirs:
            metadata_path = run_dir / "metadata.json"

            if not metadata_path.exists():
                continue

            try:
                with metadata_path.open("r", encoding="utf-8") as f:
                    metadata_dict = json.load(f)

                runs.append(
                    {
                        "run_id": run_dir.name,
                        "output_dir": str(run_dir),
                        "type": metadata_dict.get("plan", {}).get("type"),
                        "timestamp": metadata_dict.get("timestamp"),
                    }
                )

            except Exception as e:
                self.logger.warning(
                    f"Failed to read metadata for {run_dir.name}: {e}"
                )
                continue

        return runs

    def get_output_directory(self, run_id: str) -> Path:
        """Get the output directory path for a run.

        Args:
            run_id: Unique identifier for the Reel run.

        Returns:
            Path to the run's output directory.
        """
        return self.output_base / run_id

    def clean_old_runs(self, keep_count: int = 100) -> int:
        """Clean old DRY_RUN outputs, keeping only the most recent.

        Args:
            keep_count: Number of most recent runs to keep.

        Returns:
            Number of runs deleted.
        """
        if not self.output_base.exists():
            return 0

        # Get all run directories sorted by modification time
        run_dirs = sorted(
            [d for d in self.output_base.iterdir() if d.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Delete old runs
        deleted = 0
        for run_dir in run_dirs[keep_count:]:
            try:
                shutil.rmtree(run_dir)
                self.logger.info(f"Deleted old DRY_RUN output: {run_dir.name}")
                deleted += 1
            except Exception as e:
                self.logger.warning(
                    f"Failed to delete {run_dir.name}: {e}"
                )

        return deleted
