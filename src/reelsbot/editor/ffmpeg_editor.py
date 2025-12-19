"""Video editing and composition using FFmpeg.

This module provides video post-processing capabilities including text overlays,
thumbnail generation, and final composition for both A-type and E-type videos.
"""

import logging
from pathlib import Path

from reelsbot.config import ReelsbotConfig
from reelsbot.models import ReelPlan
from reelsbot.utils.ffmpeg import run_ffmpeg_command
from reelsbot.utils.paths import to_ffmpeg_path


class FFmpegEditor:
    """FFmpeg-based video editor for overlay composition and thumbnails.

    Handles post-processing of generated videos, including:
    - Text overlay for A-type videos (tagline)
    - "Fictional concept" overlay for E-type videos (CRITICAL REQUIREMENT)
    - Thumbnail extraction

    Attributes:
        config: Reelsbot configuration.
        logger: Logger instance for operation logging.

    Example:
        >>> config = load_config()
        >>> logger = setup_logger("editor")
        >>> editor = FFmpegEditor(config, logger)
        >>> final_video, thumbnail = editor.compose(raw_video, plan, output_dir)
    """

    def __init__(self, config: ReelsbotConfig, logger: logging.Logger):
        """Initialize the FFmpeg editor.

        Args:
            config: Reelsbot configuration.
            logger: Logger instance for operation logging.
        """
        self.config = config
        self.logger = logger

        # Font paths for Windows (forward slashes for FFmpeg)
        self.font_regular = "C:/Windows/Fonts/arial.ttf"
        self.font_bold = "C:/Windows/Fonts/arialbd.ttf"

    def compose_A_video(
        self,
        video_path: Path,
        plan: ReelPlan,
        output_path: Path,
    ) -> Path:
        """Add tagline text overlay to abstract video.

        Overlays the tagline text at the bottom-center of the video with
        a subtle shadow for readability.

        Args:
            video_path: Path to the raw generated video.
            plan: ReelPlan with type="A" containing tagline.
            output_path: Path where composed video should be saved.

        Returns:
            Path to the composed video file.

        Raises:
            ValueError: If plan is not A-type or missing tagline.
            RuntimeError: If FFmpeg command fails.

        Example:
            >>> final_video = editor.compose_A_video(
            ...     Path("raw_abstract.mp4"),
            ...     plan,
            ...     Path("final_abstract.mp4")
            ... )
        """
        if not plan.is_abstract():
            raise ValueError("compose_A_video requires A-type plan")
        if not plan.tagline:
            raise ValueError("A-type plan must have tagline")

        self.logger.info(f"Adding tagline overlay to A-type video: {plan.tagline}")

        # Escape special characters in tagline for FFmpeg
        tagline_escaped = self._escape_text(plan.tagline)

        # Build drawtext filter for tagline
        # Position: bottom-center (y=h-150)
        # Font: Arial Bold, 48px, white with black shadow
        drawtext_filter = (
            f"drawtext="
            f"text='{tagline_escaped}':"
            f"fontfile='{self.font_bold}':"
            f"fontsize=48:"
            f"fontcolor=white:"
            f"shadowcolor=black:"
            f"shadowx=2:"
            f"shadowy=2:"
            f"x='(w-text_w)/2':"
            f"y='h-150'"
        )

        # Build FFmpeg command
        input_ffmpeg = to_ffmpeg_path(video_path)
        output_ffmpeg = to_ffmpeg_path(output_path)

        cmd = [
            "ffmpeg",
            "-i", input_ffmpeg,
            "-vf", drawtext_filter,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-an",  # No audio
            "-y",  # Overwrite
            output_ffmpeg,
        ]

        run_ffmpeg_command(cmd, self.logger, timeout=90)

        self.logger.info(f"A-type video composed: {output_path}")
        return output_path

    def compose_E_video(
        self,
        video_path: Path,
        plan: ReelPlan,
        output_path: Path,
    ) -> Path:
        """Add "Fictional concept" overlay to E-type video.

        CRITICAL REQUIREMENT: Adds a visible "Fictional concept" label to
        clearly mark the video as containing fictional/educational content.

        The overlay consists of:
        - Black background box (450x90 pixels, 60% opacity)
        - "Fictional concept" text in white (Arial Bold, 36px)
        - Positioned at top-left (30, 30)
        - Displayed from 0.5s to end of video

        Args:
            video_path: Path to the raw generated video.
            plan: ReelPlan with type="E".
            output_path: Path where composed video should be saved.

        Returns:
            Path to the composed video file.

        Raises:
            ValueError: If plan is not E-type.
            RuntimeError: If FFmpeg command fails.

        Example:
            >>> final_video = editor.compose_E_video(
            ...     Path("raw_concept.mp4"),
            ...     plan,
            ...     Path("final_concept.mp4")
            ... )
        """
        if not plan.is_educational():
            raise ValueError("compose_E_video requires E-type plan")

        self.logger.info(
            f"Adding 'Fictional concept' overlay to E-type video: {plan.brand_name}"
        )

        # Build filter_complex for layered overlay
        # Layer 1: Draw black background box
        # Layer 2: Draw "Fictional concept" text
        # Both should appear from 0.5s onward

        drawbox_filter = (
            "drawbox="
            "x=30:y=30:"
            "w=450:h=90:"
            "color=black@0.6:"
            "t=fill:"
            "enable='gte(t,0.5)'"
        )

        drawtext_filter = (
            "drawtext="
            "text='Fictional concept':"
            f"fontfile='{self.font_bold}':"
            "fontsize=36:"
            "fontcolor=white:"
            "x=50:"
            "y=55:"
            "enable='gte(t,0.5)'"
        )

        # Combine filters
        filter_complex = f"{drawbox_filter},{drawtext_filter}"

        # Build FFmpeg command
        input_ffmpeg = to_ffmpeg_path(video_path)
        output_ffmpeg = to_ffmpeg_path(output_path)

        cmd = [
            "ffmpeg",
            "-i", input_ffmpeg,
            "-vf", filter_complex,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-an",  # No audio
            "-y",  # Overwrite
            output_ffmpeg,
        ]

        run_ffmpeg_command(cmd, self.logger, timeout=90)

        self.logger.info(f"E-type video composed with fictional concept overlay: {output_path}")
        return output_path

    def generate_thumbnail(
        self,
        video_path: Path,
        thumbnail_path: Path,
        timestamp: float = 1.0,
    ) -> Path:
        """Extract a frame from video as thumbnail image.

        Args:
            video_path: Path to the video file.
            thumbnail_path: Path where thumbnail should be saved (JPG).
            timestamp: Timestamp in seconds to extract frame from (default: 1.0).

        Returns:
            Path to the generated thumbnail file.

        Raises:
            RuntimeError: If FFmpeg command fails.

        Example:
            >>> thumb_path = editor.generate_thumbnail(
            ...     Path("final_video.mp4"),
            ...     Path("thumbnail.jpg"),
            ...     timestamp=2.0
            ... )
        """
        self.logger.info(f"Generating thumbnail from video at {timestamp}s")

        # Build FFmpeg command
        input_ffmpeg = to_ffmpeg_path(video_path)
        output_ffmpeg = to_ffmpeg_path(thumbnail_path)

        cmd = [
            "ffmpeg",
            "-i", input_ffmpeg,
            "-ss", str(timestamp),
            "-vframes", "1",
            "-q:v", "2",  # High quality JPEG
            "-y",  # Overwrite
            output_ffmpeg,
        ]

        run_ffmpeg_command(cmd, self.logger, timeout=30)

        self.logger.info(f"Thumbnail generated: {thumbnail_path}")
        return thumbnail_path

    def compose(
        self,
        video_path: Path,
        plan: ReelPlan,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """Unified entry point for video composition.

        Routes to appropriate composition method based on plan type,
        adds overlays, and generates thumbnail.

        Args:
            video_path: Path to the raw generated video.
            plan: ReelPlan for either A-type or E-type content.
            output_dir: Directory where outputs should be saved.

        Returns:
            Tuple of (final_video_path, thumbnail_path).

        Raises:
            ValueError: If plan type is invalid.
            RuntimeError: If composition or thumbnail generation fails.

        Example:
            >>> final_video, thumbnail = editor.compose(
            ...     Path("raw_video.mp4"),
            ...     plan,
            ...     Path("output")
            ... )
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output paths
        if plan.is_abstract():
            video_filename = f"final_abstract_{plan.theme}.mp4"
            thumb_filename = f"thumb_abstract_{plan.theme}.jpg"
        else:
            brand_safe = plan.brand_name.lower().replace(" ", "_")
            video_filename = f"final_concept_{brand_safe}.mp4"
            thumb_filename = f"thumb_concept_{brand_safe}.jpg"

        final_video_path = output_dir / video_filename
        thumbnail_path = output_dir / thumb_filename

        # Compose video with overlays
        if plan.is_abstract():
            self.compose_A_video(video_path, plan, final_video_path)
        else:
            self.compose_E_video(video_path, plan, final_video_path)

        # Generate thumbnail
        self.generate_thumbnail(final_video_path, thumbnail_path)

        self.logger.info(
            f"Composition complete: video={final_video_path}, "
            f"thumbnail={thumbnail_path}"
        )

        return final_video_path, thumbnail_path

    def _escape_text(self, text: str) -> str:
        """Escape special characters in text for FFmpeg drawtext filter.

        Args:
            text: Text to escape.

        Returns:
            Escaped text safe for FFmpeg drawtext.

        Example:
            >>> escaped = self._escape_text("It's a test: 50%")
            >>> print(escaped)
            It\\'s a test\\: 50\\%
        """
        # FFmpeg drawtext requires escaping: : ' [ ] , ; \ and =
        replacements = {
            "'": "\\'",
            ":": "\\:",
            "[": "\\[",
            "]": "\\]",
            ",": "\\,",
            ";": "\\;",
            "\\": "\\\\",
            "=": "\\=",
        }

        for char, escaped in replacements.items():
            text = text.replace(char, escaped)

        return text
