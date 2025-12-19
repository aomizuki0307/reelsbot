"""Data models for the reelsbot content generation pipeline.

This module defines Pydantic models for type-safe data flow throughout the system,
including content plans and metadata for generated reels.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ReelPlan(BaseModel):
    """Content plan for a single Instagram Reel.

    Represents the planned content structure before generation. Can be either
    abstract (A) or educational/fictional (E) type content.

    Attributes:
        type: Content type - "A" for abstract loops, "E" for fictional concepts.
        theme: Visual theme. For A: gradient/geometric/kinetic/particles.
               For E: category like cafe/packaging/poster/app_ui/product_design/place_concept.
        mood: Overall emotional tone (calm, dreamy, energetic, minimal, hypnotic).
        duration_sec: Video duration in seconds. A: 8-12, E: 10-14.
        tagline: Short overlay text for abstract videos (A only). 3-7 words.
        brand_name: Fictional brand name for educational content (E only). 7-14 chars.
        concept_title: Concept description for E (e.g., "Modern Cafe Interior").
        category: Content category for E (cafe, packaging, poster, etc.).
    """

    type: Literal["A", "E"] = Field(
        description="Content type: A (abstract) or E (educational/fictional)"
    )
    theme: str = Field(
        description="Visual theme or category for the content"
    )
    mood: str = Field(
        description="Emotional tone (calm, dreamy, energetic, minimal, hypnotic)"
    )
    duration_sec: int = Field(
        ge=5,
        le=60,
        description="Video duration in seconds"
    )

    # A-type specific fields
    tagline: str | None = Field(
        default=None,
        description="Short tagline for abstract videos (A only)"
    )

    # E-type specific fields
    brand_name: str | None = Field(
        default=None,
        min_length=7,
        max_length=14,
        description="Fictional brand name for educational content (E only)"
    )
    concept_title: str | None = Field(
        default=None,
        description="Concept description for E-type content"
    )
    category: str | None = Field(
        default=None,
        description="Category for E-type (cafe, packaging, poster, etc.)"
    )

    @field_validator("duration_sec")
    @classmethod
    def validate_duration(cls, v: int, info) -> int:
        """Validate duration is within acceptable ranges for content type.

        Args:
            v: Duration value in seconds.
            info: Validation context.

        Returns:
            Validated duration value.

        Note:
            Type-specific validation (A: 8-12, E: 10-14) is enforced in the planner,
            not here, to keep the model flexible.
        """
        return v

    @field_validator("type")
    @classmethod
    def validate_type_fields(cls, v: str) -> str:
        """Ensure content type is valid.

        Args:
            v: Type value.

        Returns:
            Validated type value.
        """
        return v

    def model_post_init(self, __context) -> None:
        """Validate type-specific required fields after initialization.

        Raises:
            ValueError: If required fields are missing for the content type.
        """
        if self.type == "A":
            if not self.tagline:
                raise ValueError("A-type content requires 'tagline' field")
        elif self.type == "E":
            if not self.brand_name:
                raise ValueError("E-type content requires 'brand_name' field")
            if not self.concept_title:
                raise ValueError("E-type content requires 'concept_title' field")
            if not self.category:
                raise ValueError("E-type content requires 'category' field")

    def is_abstract(self) -> bool:
        """Check if this is an abstract (A) type plan.

        Returns:
            True if type is A, False otherwise.
        """
        return self.type == "A"

    def is_educational(self) -> bool:
        """Check if this is an educational/fictional (E) type plan.

        Returns:
            True if type is E, False otherwise.
        """
        return self.type == "E"

    def get_display_title(self) -> str:
        """Get a human-readable title for this plan.

        Returns:
            Display title string.
        """
        if self.type == "A":
            return f"{self.theme.title()} - {self.tagline}"
        else:
            return f"{self.brand_name} - {self.concept_title}"


class ReelMetadata(BaseModel):
    """Complete metadata for a generated Instagram Reel.

    Contains all information about a generated reel, including the plan,
    generated caption, output paths, and publication status.

    Attributes:
        run_id: Unique identifier for this generation run.
        timestamp: When the reel was generated.
        plan: The content plan used for generation.
        caption: Generated caption text for Instagram.
        hashtags: List of hashtags for the post.
        video_path: Path to the generated video file.
        thumbnail_path: Path to the generated thumbnail image.
        status: Current status of the reel (generated, failed, published).
    """

    run_id: str = Field(
        description="Unique run identifier"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Generation timestamp"
    )
    plan: ReelPlan = Field(
        description="Content plan for this reel"
    )
    caption: str = Field(
        description="Generated Instagram caption"
    )
    hashtags: list[str] = Field(
        default_factory=list,
        description="List of hashtags for the post"
    )
    video_path: Path = Field(
        description="Path to generated video file"
    )
    thumbnail_path: Path = Field(
        description="Path to generated thumbnail image"
    )
    status: Literal["generated", "failed", "published"] = Field(
        default="generated",
        description="Publication status"
    )

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, v: list[str]) -> list[str]:
        """Validate hashtag format.

        Args:
            v: List of hashtags.

        Returns:
            Validated hashtag list.

        Raises:
            ValueError: If hashtags are invalid.
        """
        # Ensure hashtags don't start with #
        cleaned = []
        for tag in v:
            tag = tag.strip()
            if tag.startswith("#"):
                tag = tag[1:]
            if tag:
                cleaned.append(tag)
        return cleaned

    @field_validator("video_path", "thumbnail_path")
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        """Validate file paths.

        Args:
            v: Path value.

        Returns:
            Validated path.
        """
        # Convert to Path if string
        if isinstance(v, str):
            return Path(v)
        return v

    def get_hashtags_string(self) -> str:
        """Get hashtags formatted for Instagram caption.

        Returns:
            Space-separated hashtags with # prefix.
        """
        return " ".join(f"#{tag}" for tag in self.hashtags)

    def get_full_caption(self) -> str:
        """Get complete caption with hashtags.

        Returns:
            Caption text followed by hashtags.
        """
        if self.hashtags:
            return f"{self.caption}\n\n{self.get_hashtags_string()}"
        return self.caption

    def is_published(self) -> bool:
        """Check if this reel has been published.

        Returns:
            True if status is published, False otherwise.
        """
        return self.status == "published"

    def is_failed(self) -> bool:
        """Check if this reel generation failed.

        Returns:
            True if status is failed, False otherwise.
        """
        return self.status == "failed"

    def to_summary_dict(self) -> dict:
        """Convert to a summary dictionary for logging/display.

        Returns:
            Dictionary with key metadata fields.
        """
        return {
            "run_id": self.run_id,
            "type": self.plan.type,
            "title": self.plan.get_display_title(),
            "duration": self.plan.duration_sec,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
        }

    class Config:
        """Pydantic model configuration."""

        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }
