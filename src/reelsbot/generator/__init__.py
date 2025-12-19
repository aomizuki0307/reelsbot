"""Video generation modules for reelsbot.

This package provides video generation engines for creating Instagram Reels
content. Includes both abstract (A-type) and educational/fictional (E-type)
video generators.
"""

from reelsbot.generator.base import BaseGenerator
from reelsbot.generator.ffmpeg_dummy import FFmpegDummyGenerator

__all__ = [
    "BaseGenerator",
    "FFmpegDummyGenerator",
]
