"""Utility modules for reelsbot."""

from reelsbot.utils.brand_name import BrandNameGenerator, generate_brand_name
from reelsbot.utils.ffmpeg import (
    build_filter_complex,
    check_ffmpeg_available,
    convert_to_h264,
    get_video_info,
    run_ffmpeg_command,
)
from reelsbot.utils.image import (
    CATEGORY_COLORS,
    add_text_to_image,
    create_concept_background,
    create_thumbnail_from_image,
)
from reelsbot.utils.logger import get_logger, setup_logger, update_run_id
from reelsbot.utils.paths import (
    ensure_dir,
    ensure_output_dir,
    get_temp_path,
    safe_filename,
    to_ffmpeg_path,
)

__all__ = [
    # Brand name generation
    "BrandNameGenerator",
    "generate_brand_name",
    # FFmpeg utilities
    "check_ffmpeg_available",
    "run_ffmpeg_command",
    "build_filter_complex",
    "get_video_info",
    "convert_to_h264",
    # Image utilities
    "create_concept_background",
    "add_text_to_image",
    "create_thumbnail_from_image",
    "CATEGORY_COLORS",
    # Logging
    "setup_logger",
    "get_logger",
    "update_run_id",
    # Path utilities
    "to_ffmpeg_path",
    "ensure_output_dir",
    "ensure_dir",
    "safe_filename",
    "get_temp_path",
]
