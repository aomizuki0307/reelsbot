"""Demo script for Phase 3 video generation and editing.

This example demonstrates how to use the FFmpegDummyGenerator and FFmpegEditor
to create both A-type (abstract) and E-type (fictional concept) videos.

Usage:
    python examples/demo_video_generation.py

Note:
    Requires FFmpeg to be installed and available in PATH.
    Install FFmpeg from: https://ffmpeg.org/download.html
"""

from pathlib import Path

from reelsbot import create_llm_client, load_config
from reelsbot.editor import FFmpegEditor
from reelsbot.generator import FFmpegDummyGenerator
from reelsbot.models import ReelPlan
from reelsbot.utils import check_ffmpeg_available, setup_logger


def demo_a_type_generation():
    """Demonstrate A-type abstract video generation."""
    print("\n" + "=" * 60)
    print("Demo 1: A-Type Abstract Video Generation")
    print("=" * 60)

    # Load config and setup logger
    config = load_config()
    logger = setup_logger("demo_a_type")

    # Create output directory
    output_dir = Path("output/demo_a_type")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create A-type plan
    plan = ReelPlan(
        type="A",
        theme="gradient",
        mood="calm",
        duration_sec=10,
        tagline="A moment of peace",
    )

    print(f"\nPlan: {plan.get_display_title()}")
    print(f"  Theme: {plan.theme}")
    print(f"  Mood: {plan.mood}")
    print(f"  Duration: {plan.duration_sec}s")

    # Initialize generator and editor
    generator = FFmpegDummyGenerator(config, logger)
    editor = FFmpegEditor(config, logger)

    # Generate raw video
    print("\n[1/3] Generating raw abstract video...")
    raw_video_path = generator.generate_A_video(
        plan, output_dir / "raw_abstract.mp4"
    )
    print(f"  Generated: {raw_video_path}")

    # Compose with tagline overlay
    print("\n[2/3] Adding tagline overlay...")
    final_video_path, thumbnail_path = editor.compose(
        raw_video_path, plan, output_dir
    )
    print(f"  Final video: {final_video_path}")
    print(f"  Thumbnail: {thumbnail_path}")

    print("\n✓ A-type video generation complete!")
    print(f"  Output directory: {output_dir.absolute()}")


def demo_e_type_generation():
    """Demonstrate E-type fictional concept video generation."""
    print("\n" + "=" * 60)
    print("Demo 2: E-Type Fictional Concept Video Generation")
    print("=" * 60)

    # Load config and setup logger
    config = load_config()
    logger = setup_logger("demo_e_type")

    # Create output directory
    output_dir = Path("output/demo_e_type")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create E-type plan
    plan = ReelPlan(
        type="E",
        theme="cafe",
        mood="calm",
        duration_sec=12,
        brand_name="ZENITHCAFE",
        concept_title="Modern Cafe Interior",
        category="cafe",
    )

    print(f"\nPlan: {plan.get_display_title()}")
    print(f"  Brand: {plan.brand_name}")
    print(f"  Concept: {plan.concept_title}")
    print(f"  Category: {plan.category}")
    print(f"  Duration: {plan.duration_sec}s")

    # Initialize generator and editor
    generator = FFmpegDummyGenerator(config, logger)
    editor = FFmpegEditor(config, logger)

    # Generate raw video
    print("\n[1/3] Generating raw concept video...")
    raw_video_path = generator.generate_E_video(
        plan, output_dir / "raw_concept.mp4"
    )
    print(f"  Generated: {raw_video_path}")

    # Compose with "Fictional concept" overlay (CRITICAL)
    print("\n[2/3] Adding 'Fictional concept' overlay...")
    final_video_path, thumbnail_path = editor.compose(
        raw_video_path, plan, output_dir
    )
    print(f"  Final video: {final_video_path}")
    print(f"  Thumbnail: {thumbnail_path}")

    print("\n✓ E-type video generation complete!")
    print(f"  Output directory: {output_dir.absolute()}")
    print("\n  IMPORTANT: The video includes the 'Fictional concept' overlay")
    print("  as required to mark fictional/educational content.")


def demo_all_themes():
    """Demonstrate all A-type themes."""
    print("\n" + "=" * 60)
    print("Demo 3: All A-Type Themes")
    print("=" * 60)

    # Load config and setup logger
    config = load_config()
    logger = setup_logger("demo_themes")

    # Create output directory
    output_dir = Path("output/demo_all_themes")
    output_dir.mkdir(parents=True, exist_ok=True)

    # All themes
    themes = [
        ("gradient", "calm", "Flowing colors"),
        ("geometric", "energetic", "Abstract shapes"),
        ("kinetic", "hypnotic", "Moving patterns"),
        ("particles", "dreamy", "Digital noise"),
    ]

    generator = FFmpegDummyGenerator(config, logger)
    editor = FFmpegEditor(config, logger)

    for i, (theme, mood, tagline) in enumerate(themes, 1):
        print(f"\n[{i}/{len(themes)}] Generating {theme} theme...")

        plan = ReelPlan(
            type="A",
            theme=theme,
            mood=mood,
            duration_sec=8,
            tagline=tagline,
        )

        # Generate and compose
        raw_path = output_dir / f"raw_{theme}.mp4"
        raw_video = generator.generate_A_video(plan, raw_path)
        final_video, thumbnail = editor.compose(raw_video, plan, output_dir)

        print(f"  ✓ {theme}: {final_video.name}")

    print("\n✓ All themes generated!")
    print(f"  Output directory: {output_dir.absolute()}")


def main():
    """Run all demos."""
    print("\nReelsbot Phase 3: Video Generation & Editing Demo")
    print("=" * 60)

    # Check FFmpeg availability
    print("\nChecking FFmpeg availability...")
    if not check_ffmpeg_available():
        print("\n❌ ERROR: FFmpeg is not available!")
        print("\nPlease install FFmpeg and add it to your PATH:")
        print("  Windows: https://ffmpeg.org/download.html")
        print("  Or use: winget install ffmpeg")
        return

    print("✓ FFmpeg is available")

    # Run demos
    try:
        demo_a_type_generation()
        demo_e_type_generation()
        demo_all_themes()

        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        print("\nGenerated files are in the 'output/' directory.")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
