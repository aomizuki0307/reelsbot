"""FFmpeg-based video generator without external APIs.

This module implements video generation using pure FFmpeg filters for A-type
abstract videos and PIL + FFmpeg for E-type fictional concept videos.
No external APIs or asset libraries are required.
"""

import logging
import tempfile
from pathlib import Path

from reelsbot.config import ReelsbotConfig
from reelsbot.generator.base import BaseGenerator
from reelsbot.models import ReelPlan
from reelsbot.utils.ffmpeg import run_ffmpeg_command
from reelsbot.utils.image import create_concept_background
from reelsbot.utils.paths import to_ffmpeg_path


class FFmpegDummyGenerator(BaseGenerator):
    """FFmpeg-based video generator for both A and E type content.

    Generates videos using only FFmpeg filters (A-type) and PIL images with
    FFmpeg motion (E-type). No external APIs required.

    Attributes:
        config: Reelsbot configuration.
        logger: Logger instance for operation logging.

    Example:
        >>> config = load_config()
        >>> logger = setup_logger("generator")
        >>> generator = FFmpegDummyGenerator(config, logger)
        >>> video_path = generator.generate(plan, output_dir)
    """

    def __init__(self, config: ReelsbotConfig, logger: logging.Logger):
        """Initialize the FFmpeg dummy generator.

        Args:
            config: Reelsbot configuration.
            logger: Logger instance for operation logging.
        """
        self.config = config
        self.logger = logger

    def generate_A_video(self, plan: ReelPlan, output_path: Path) -> Path:
        """Generate abstract loop video for A-type content using FFmpeg filters.

        Creates a visually engaging abstract video based on the theme. Uses
        different FFmpeg filter chains for each theme type.

        Args:
            plan: ReelPlan with type="A".
            output_path: Path where video should be saved.

        Returns:
            Path to the generated video file.

        Raises:
            ValueError: If plan is not A-type.
            RuntimeError: If FFmpeg command fails.
        """
        self.validate_plan(plan, "A")

        self.logger.info(
            f"Generating A-type video: theme={plan.theme}, "
            f"mood={plan.mood}, duration={plan.duration_sec}s"
        )

        # Get theme-specific filter
        filter_cmd = self._get_theme_filter(plan.theme, plan.duration_sec)

        # Build FFmpeg command
        output_ffmpeg = to_ffmpeg_path(output_path)

        # Execute FFmpeg command
        run_ffmpeg_command(filter_cmd + [output_ffmpeg], self.logger, timeout=60)

        self.logger.info(f"A-type video generated: {output_path}")
        return output_path

    def generate_E_video(self, plan: ReelPlan, output_path: Path) -> Path:
        """Generate fictional concept video for E-type content.

        Two-stage process:
        1. Create background image with PIL (brand name, concept, category shape)
        2. Apply camera motion with FFmpeg (slow zoom/pan)

        Args:
            plan: ReelPlan with type="E".
            output_path: Path where video should be saved.

        Returns:
            Path to the generated video file.

        Raises:
            ValueError: If plan is not E-type.
            RuntimeError: If image creation or FFmpeg command fails.
        """
        self.validate_plan(plan, "E")

        self.logger.info(
            f"Generating E-type video: brand={plan.brand_name}, "
            f"concept={plan.concept_title}, duration={plan.duration_sec}s"
        )

        # Stage 1: Create background image with PIL
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bg_image_path = create_concept_background(plan, temp_path)

            self.logger.debug(f"Background image created: {bg_image_path}")

            # Stage 2: Apply camera motion with FFmpeg
            bg_ffmpeg = to_ffmpeg_path(bg_image_path)
            output_ffmpeg = to_ffmpeg_path(output_path)

            # Calculate zoompan parameters for smooth motion
            # Start slightly zoomed out, slowly zoom in
            duration = plan.duration_sec
            total_frames = duration * 30  # 30 fps

            # Zoompan filter: zoom from 1.0 to 1.3 over duration
            # Position: start from center
            zoompan_filter = (
                f"zoompan=z='min(zoom+0.002,1.3)'"
                f":x='iw/2-(iw/zoom/2)'"
                f":y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}"
                f":s=1080x1920"
            )

            cmd = [
                "ffmpeg",
                "-loop", "1",
                "-i", bg_ffmpeg,
                "-vf", zoompan_filter,
                "-t", str(duration),
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-an",  # No audio
                "-y",  # Overwrite
                output_ffmpeg,
            ]

            run_ffmpeg_command(cmd, self.logger, timeout=90)

        self.logger.info(f"E-type video generated: {output_path}")
        return output_path

    def _get_theme_filter(self, theme: str, duration: int) -> list[str]:
        """Get FFmpeg filter command for the specified theme.

        Args:
            theme: Theme name (gradient, geometric, kinetic, particles).
            duration: Video duration in seconds.

        Returns:
            FFmpeg command as list of arguments (without output path).

        Raises:
            ValueError: If theme is unknown.
        """
        theme = theme.lower()

        if theme == "gradient":
            # Dynamic color gradients using lavfi and geq filter
            return [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c=0x3A86FF:s=1080x1920:d={duration}",
                "-vf", (
                    "geq="
                    "'r=128+128*sin(Y/100+T*2):"
                    "g=128+128*sin(X/100+T*3):"
                    "b=255'"
                ),
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-t", str(duration),
                "-an",
                "-y",
            ]

        elif theme == "geometric":
            # Rotating geometric patterns using testsrc2
            return [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"testsrc2=s=1080x1920:d={duration}:r=30",
                "-vf", (
                    f"rotate=t*PI/5:c=0x1E1E2E:ow=1080:oh=1920"
                ),
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-an",
                "-y",
            ]

        elif theme == "kinetic":
            # Animated moving boxes using drawbox
            return [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c=0x1A1A2E:s=1080x1920:d={duration}",
                "-vf", (
                    "drawbox="
                    "x='100+200*sin(t*2)':y='200+300*cos(t*1.5)':"
                    "w=200:h=200:color=0x0F3460@0.7:t=fill,"
                    "drawbox="
                    "x='500+150*cos(t*1.8)':y='800+250*sin(t*2.2)':"
                    "w=150:h=150:color=0x16213E@0.6:t=fill,"
                    "drawbox="
                    "x='300+180*sin(t*1.3)':y='1400+200*cos(t*1.7)':"
                    "w=180:h=180:color=0x533483@0.8:t=fill"
                ),
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-t", str(duration),
                "-an",
                "-y",
            ]

        elif theme == "particles":
            # Particle-like effect using noise and motion
            return [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"nullsrc=s=1080x1920:d={duration}",
                "-vf", (
                    "geq="
                    "'r=random(1)*255:"
                    "g=random(1)*255:"
                    "b=random(1)*255',"
                    "boxblur=5:1"
                ),
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-t", str(duration),
                "-an",
                "-y",
            ]

        else:
            # Default to gradient if theme unknown
            self.logger.warning(
                f"Unknown theme '{theme}', using gradient as default"
            )
            return self._get_theme_filter("gradient", duration)
