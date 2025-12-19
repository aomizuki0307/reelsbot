"""Base publisher interface for Instagram Reels.

This module defines the abstract base class for all publisher implementations,
ensuring a consistent interface for publishing generated Reels.
"""

from abc import ABC, abstractmethod
from typing import Any

from reelsbot.models import ReelMetadata


class PublisherError(Exception):
    """Exception raised for errors during publishing operations."""

    pass


class BasePublisher(ABC):
    """Abstract base class for Reel publishers.

    Defines the interface that all publisher implementations must follow,
    whether publishing to Instagram, saving locally, or other destinations.

    All publishers must implement:
    - publish(): Publish a reel and return result
    - get_status(): Check publication status of a reel
    """

    @abstractmethod
    async def publish(self, metadata: ReelMetadata) -> dict[str, Any]:
        """Publish a Reel to the target platform.

        Args:
            metadata: Complete Reel metadata including video path, caption, etc.

        Returns:
            Dictionary with publication result:
                - status: Publication status (success, failed, etc.)
                - Additional platform-specific fields

        Raises:
            PublisherError: If publication fails.

        Examples:
            >>> result = await publisher.publish(metadata)
            >>> if result["status"] == "success":
            ...     print(f"Published: {result['url']}")
        """
        pass

    @abstractmethod
    def get_status(self, run_id: str) -> dict[str, Any]:
        """Get the publication status of a Reel.

        Args:
            run_id: Unique identifier for the Reel run.

        Returns:
            Dictionary with status information:
                - status: Current status
                - Additional platform-specific fields

        Raises:
            PublisherError: If status check fails.

        Examples:
            >>> status = publisher.get_status(run_id)
            >>> print(f"Status: {status['status']}")
        """
        pass

    def validate_metadata(self, metadata: ReelMetadata) -> None:
        """Validate metadata before publishing.

        Checks that all required fields are present and files exist.

        Args:
            metadata: Metadata to validate.

        Raises:
            PublisherError: If validation fails.
        """
        # Check required fields
        if not metadata.run_id:
            raise PublisherError("Missing run_id in metadata")

        if not metadata.caption:
            raise PublisherError("Missing caption in metadata")

        if not metadata.video_path:
            raise PublisherError("Missing video_path in metadata")

        # Check file existence
        if not metadata.video_path.exists():
            raise PublisherError(
                f"Video file not found: {metadata.video_path}"
            )

        if metadata.thumbnail_path and not metadata.thumbnail_path.exists():
            raise PublisherError(
                f"Thumbnail file not found: {metadata.thumbnail_path}"
            )
