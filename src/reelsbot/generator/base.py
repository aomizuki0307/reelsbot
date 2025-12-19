"""Abstract base class for video generators.

This module defines the interface that all video generators must implement,
providing a consistent API for generating A-type (abstract) and E-type
(educational/fictional) videos.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from reelsbot.models import ReelPlan


class BaseGenerator(ABC):
    """Abstract base class for video generation engines.

    All video generators must inherit from this class and implement the
    abstract methods for generating A-type and E-type videos. The unified
    `generate()` method provides automatic routing based on plan type.

    Example:
        >>> class MyGenerator(BaseGenerator):
        ...     def generate_A_video(self, plan, output_path):
        ...         # Generate abstract video
        ...         return output_path
        ...
        ...     def generate_E_video(self, plan, output_path):
        ...         # Generate educational video
        ...         return output_path
        ...
        >>> generator = MyGenerator()
        >>> video_path = generator.generate(plan, output_dir)
    """

    @abstractmethod
    def generate_A_video(self, plan: ReelPlan, output_path: Path) -> Path:
        """Generate an abstract loop video for A-type content.

        Creates a visually engaging abstract video based on the plan's theme,
        mood, and duration. The video should be a seamless loop suitable for
        Instagram Reels.

        Args:
            plan: ReelPlan with type="A" containing theme, mood, duration, and tagline.
            output_path: Path where the generated video should be saved.

        Returns:
            Path to the generated video file (should be same as output_path).

        Raises:
            ValueError: If plan is not A-type or missing required fields.
            RuntimeError: If video generation fails.

        Requirements:
            - Resolution: 1080x1920 (9:16 aspect ratio)
            - Frame rate: 30fps
            - Duration: plan.duration_sec (typically 8-12 seconds)
            - Codec: H.264 (libx264), yuv420p pixel format
            - Audio: None (silent video)
            - Loop: Should transition smoothly from end to start

        Example:
            >>> plan = ReelPlan(
            ...     type="A",
            ...     theme="gradient",
            ...     mood="calm",
            ...     duration_sec=10,
            ...     tagline="A moment of peace"
            ... )
            >>> video_path = generator.generate_A_video(plan, Path("abstract.mp4"))
        """
        pass

    @abstractmethod
    def generate_E_video(self, plan: ReelPlan, output_path: Path) -> Path:
        """Generate a fictional concept video for E-type content.

        Creates an educational video showcasing a fictional brand and design
        concept. The video should present the concept clearly with appropriate
        branding and visual styling.

        Args:
            plan: ReelPlan with type="E" containing brand_name, concept_title,
                  category, and duration.
            output_path: Path where the generated video should be saved.

        Returns:
            Path to the generated video file (should be same as output_path).

        Raises:
            ValueError: If plan is not E-type or missing required fields.
            RuntimeError: If video generation fails.

        Requirements:
            - Resolution: 1080x1920 (9:16 aspect ratio)
            - Frame rate: 30fps
            - Duration: plan.duration_sec (typically 10-14 seconds)
            - Codec: H.264 (libx264), yuv420p pixel format
            - Audio: None (silent video)
            - Content: Display brand name and concept clearly
            - Motion: Subtle camera movement (zoom/pan)

        Example:
            >>> plan = ReelPlan(
            ...     type="E",
            ...     theme="cafe",
            ...     mood="calm",
            ...     duration_sec=12,
            ...     brand_name="ZENITH",
            ...     concept_title="Modern Cafe Interior",
            ...     category="cafe"
            ... )
            >>> video_path = generator.generate_E_video(plan, Path("concept.mp4"))
        """
        pass

    def generate(self, plan: ReelPlan, output_dir: Path) -> Path:
        """Unified entry point for video generation.

        Automatically routes to the appropriate generation method (A or E)
        based on the plan type. Creates output directory if needed and
        generates output filename.

        Args:
            plan: ReelPlan for either A-type or E-type content.
            output_dir: Directory where the video should be saved.

        Returns:
            Path to the generated video file.

        Raises:
            ValueError: If plan type is invalid or missing required fields.
            RuntimeError: If video generation fails.

        Example:
            >>> plan = ReelPlan(type="A", theme="gradient", ...)
            >>> video_path = generator.generate(plan, Path("output"))
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename based on type
        if plan.is_abstract():
            filename = f"abstract_{plan.theme}_{plan.duration_sec}s.mp4"
        elif plan.is_educational():
            brand_safe = plan.brand_name.lower().replace(" ", "_")
            filename = f"concept_{brand_safe}_{plan.duration_sec}s.mp4"
        else:
            raise ValueError(f"Invalid plan type: {plan.type}")

        output_path = output_dir / filename

        # Route to appropriate generator
        if plan.is_abstract():
            return self.generate_A_video(plan, output_path)
        else:
            return self.generate_E_video(plan, output_path)

    def validate_plan(self, plan: ReelPlan, expected_type: str) -> None:
        """Validate that a plan matches the expected type and has required fields.

        Args:
            plan: ReelPlan to validate.
            expected_type: Expected type ("A" or "E").

        Raises:
            ValueError: If plan type doesn't match or required fields are missing.

        Example:
            >>> self.validate_plan(plan, "A")
        """
        if plan.type != expected_type:
            raise ValueError(
                f"Expected {expected_type}-type plan, got {plan.type}-type"
            )

        # Validate type-specific fields
        if expected_type == "A":
            if not plan.tagline:
                raise ValueError("A-type plan must have tagline")
        elif expected_type == "E":
            if not plan.brand_name:
                raise ValueError("E-type plan must have brand_name")
            if not plan.concept_title:
                raise ValueError("E-type plan must have concept_title")
            if not plan.category:
                raise ValueError("E-type plan must have category")
