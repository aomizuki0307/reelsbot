"""Verification script for Phase 3 implementation.

This script verifies that all Phase 3 modules can be imported correctly
and that the basic structure is in place.

Usage:
    python scripts/verify_phase3.py
"""

import sys
from pathlib import Path


def verify_imports():
    """Verify all Phase 3 modules can be imported."""
    print("Phase 3 Implementation Verification")
    print("=" * 60)

    errors = []

    # Test 1: Import generator base
    print("\n[1/9] Testing generator.base imports...")
    try:
        from reelsbot.generator.base import BaseGenerator
        print("  ✓ BaseGenerator imported successfully")
    except Exception as e:
        errors.append(f"BaseGenerator: {e}")
        print(f"  ✗ BaseGenerator import failed: {e}")

    # Test 2: Import FFmpeg dummy generator
    print("\n[2/9] Testing generator.ffmpeg_dummy imports...")
    try:
        from reelsbot.generator.ffmpeg_dummy import FFmpegDummyGenerator
        print("  ✓ FFmpegDummyGenerator imported successfully")
    except Exception as e:
        errors.append(f"FFmpegDummyGenerator: {e}")
        print(f"  ✗ FFmpegDummyGenerator import failed: {e}")

    # Test 3: Import FFmpeg editor
    print("\n[3/9] Testing editor.ffmpeg_editor imports...")
    try:
        from reelsbot.editor.ffmpeg_editor import FFmpegEditor
        print("  ✓ FFmpegEditor imported successfully")
    except Exception as e:
        errors.append(f"FFmpegEditor: {e}")
        print(f"  ✗ FFmpegEditor import failed: {e}")

    # Test 4: Import FFmpeg utilities
    print("\n[4/9] Testing utils.ffmpeg imports...")
    try:
        from reelsbot.utils.ffmpeg import (
            check_ffmpeg_available,
            run_ffmpeg_command,
            build_filter_complex,
            get_video_info,
            convert_to_h264,
        )
        print("  ✓ FFmpeg utilities imported successfully")
    except Exception as e:
        errors.append(f"FFmpeg utilities: {e}")
        print(f"  ✗ FFmpeg utilities import failed: {e}")

    # Test 5: Import image utilities
    print("\n[5/9] Testing utils.image imports...")
    try:
        from reelsbot.utils.image import (
            create_concept_background,
            add_text_to_image,
            create_thumbnail_from_image,
            CATEGORY_COLORS,
        )
        print("  ✓ Image utilities imported successfully")
    except Exception as e:
        errors.append(f"Image utilities: {e}")
        print(f"  ✗ Image utilities import failed: {e}")

    # Test 6: Import from generator package
    print("\n[6/9] Testing generator package exports...")
    try:
        from reelsbot.generator import BaseGenerator, FFmpegDummyGenerator
        print("  ✓ Generator package exports working")
    except Exception as e:
        errors.append(f"Generator package: {e}")
        print(f"  ✗ Generator package import failed: {e}")

    # Test 7: Import from editor package
    print("\n[7/9] Testing editor package exports...")
    try:
        from reelsbot.editor import FFmpegEditor
        print("  ✓ Editor package exports working")
    except Exception as e:
        errors.append(f"Editor package: {e}")
        print(f"  ✗ Editor package import failed: {e}")

    # Test 8: Import from utils package
    print("\n[8/9] Testing utils package exports...")
    try:
        from reelsbot.utils import (
            check_ffmpeg_available,
            create_concept_background,
        )
        print("  ✓ Utils package exports working")
    except Exception as e:
        errors.append(f"Utils package: {e}")
        print(f"  ✗ Utils package import failed: {e}")

    # Test 9: Verify FFmpeg availability
    print("\n[9/9] Checking FFmpeg availability...")
    try:
        from reelsbot.utils.ffmpeg import check_ffmpeg_available
        if check_ffmpeg_available():
            print("  ✓ FFmpeg is available in PATH")
        else:
            print("  ⚠ FFmpeg is NOT available (required for video generation)")
            print("    Install from: https://ffmpeg.org/download.html")
    except Exception as e:
        errors.append(f"FFmpeg check: {e}")
        print(f"  ✗ FFmpeg check failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"\n❌ Verification FAILED with {len(errors)} error(s):\n")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All Phase 3 modules verified successfully!")
        print("\nPhase 3 is ready to use.")
        print("\nNext steps:")
        print("  1. Install FFmpeg if not available")
        print("  2. Run demo: python examples/demo_video_generation.py")
        print("  3. Run tests: pytest tests/test_phase3_integration.py -v")
        return True


def verify_file_structure():
    """Verify all Phase 3 files exist."""
    print("\n" + "=" * 60)
    print("File Structure Verification")
    print("=" * 60)

    base_path = Path("src/reelsbot")

    files = [
        "generator/__init__.py",
        "generator/base.py",
        "generator/ffmpeg_dummy.py",
        "editor/__init__.py",
        "editor/ffmpeg_editor.py",
        "utils/ffmpeg.py",
        "utils/image.py",
    ]

    missing = []

    for file_path in files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (MISSING)")
            missing.append(file_path)

    if missing:
        print(f"\n❌ {len(missing)} file(s) missing")
        return False
    else:
        print("\n✓ All Phase 3 files present")
        return True


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("Reelsbot Phase 3 Verification Script")
    print("=" * 60)

    # Change to project root
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / "src"))

    # Run verifications
    structure_ok = verify_file_structure()
    imports_ok = verify_imports()

    # Final result
    print("\n" + "=" * 60)
    if structure_ok and imports_ok:
        print("✅ Phase 3 verification PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ Phase 3 verification FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
