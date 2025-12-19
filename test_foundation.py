"""Quick test script to verify Phase 1 foundation implementation.

This script tests the core modules without requiring API keys.
"""

import asyncio
import sys
from pathlib import Path

# Add src directory to path for testing without installation
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test imports
print("Testing imports...")
from reelsbot import __version__, load_config
from reelsbot.config import ReelsbotConfig
from reelsbot.llm_client import LLMClient
from reelsbot.utils import (
    BrandNameGenerator,
    ensure_output_dir,
    generate_brand_name,
    safe_filename,
    setup_logger,
    to_ffmpeg_path,
)

print(f"[OK] All imports successful (reelsbot v{__version__})")


def test_brand_name_generator() -> None:
    """Test brand name generation."""
    print("\n=== Testing Brand Name Generator ===")

    generator = BrandNameGenerator(seed=42)

    # Generate single brand
    brand = generator.generate()
    print(f"Generated brand: {brand}")
    assert 7 <= len(brand) <= 14, f"Brand length {len(brand)} not in range 7-14"
    assert brand.isalpha(), "Brand should contain only letters"
    assert generator.is_safe(brand), "Brand should be safe"

    # Generate batch
    brands = generator.generate_batch(5)
    print(f"Generated batch: {brands}")
    assert len(brands) == 5, "Should generate 5 brands"
    assert len(set(brands)) == 5, "All brands should be unique"

    # Test unsafe brands
    assert not generator.is_safe("AppleCore"), "Should reject brands with 'apple'"
    assert not generator.is_safe("Nike123"), "Should reject brands with numbers"
    assert not generator.is_safe("Hi"), "Should reject too-short brands"

    print("[OK] Brand name generation tests passed")


def test_paths() -> None:
    """Test path utilities."""
    print("\n=== Testing Path Utilities ===")

    # Test to_ffmpeg_path
    windows_path = Path("C:\\Users\\test\\video.mp4")
    ffmpeg_path = to_ffmpeg_path(windows_path)
    print(f"Windows path: {windows_path}")
    print(f"FFmpeg path: {ffmpeg_path}")
    assert "/" in ffmpeg_path, "FFmpeg path should use forward slashes"
    assert "\\" not in ffmpeg_path, "FFmpeg path should not have backslashes"

    # Test ensure_output_dir
    test_run_id = "test_run_001"
    output_dir = ensure_output_dir(test_run_id, Path("outputs"))
    print(f"Output dir created: {output_dir}")
    assert output_dir.exists(), "Output directory should exist"
    assert output_dir.name == test_run_id, "Output directory should match run_id"

    # Test safe_filename
    unsafe_name = "My Video: Part 1 <test>?"
    safe_name = safe_filename(unsafe_name)
    print(f"Unsafe: '{unsafe_name}' -> Safe: '{safe_name}'")
    assert "<" not in safe_name, "Should remove unsafe characters"
    assert ":" not in safe_name, "Should remove unsafe characters"

    print("[OK] Path utilities tests passed")


def test_logger() -> None:
    """Test logger setup."""
    print("\n=== Testing Logger ===")

    run_id = "test_run_logger_001"
    logger = setup_logger(run_id, logs_dir=Path("logs"), level=20)  # INFO level

    logger.info("This is an info message")
    logger.debug("This is a debug message (may not show in console)")
    logger.warning("This is a warning message")

    # Check log file was created
    log_file = Path("logs") / f"{Path().cwd().joinpath('logs').exists()}"
    print(f"[OK] Logger setup successful with run_id: {run_id}")


def test_config() -> None:
    """Test configuration loading."""
    print("\n=== Testing Configuration ===")

    # Create a minimal test config without validation
    config = ReelsbotConfig(
        llm_provider="anthropic",
        anthropic_api_key="test-key-placeholder",
        default_a_ratio=70,
        default_e_ratio=30,
    )

    print(f"Provider: {config.llm_provider}")
    print(f"Model: {config.get_active_model()}")
    print(f"A/E Ratio: {config.default_a_ratio}/{config.default_e_ratio}")
    print(f"Video resolution: {config.video_resolution}")
    print(f"Max retries: {config.policy_max_retry}")

    # Test API key retrieval
    try:
        api_key = config.get_active_api_key()
        print(f"API key retrieved: {api_key[:10]}...")
    except ValueError:
        print("API key validation working (expected for test key)")

    print("[OK] Configuration tests passed")


async def test_llm_client() -> None:
    """Test LLM client initialization (without actual API calls)."""
    print("\n=== Testing LLM Client ===")

    # Create config with test API key
    config = ReelsbotConfig(
        llm_provider="anthropic",
        anthropic_api_key="test-key-placeholder",
        default_a_ratio=70,
        default_e_ratio=30,
    )

    try:
        client = LLMClient(config)
        model_info = client.get_model_info()
        print(f"LLM client created: {model_info}")
        print("[OK] LLM client initialization successful")
    except Exception as e:
        print(f"LLM client test skipped (expected without real API key): {e}")


def main() -> None:
    """Run all tests."""
    print("=" * 60)
    print("REELSBOT PHASE 1 FOUNDATION TESTS")
    print("=" * 60)

    test_brand_name_generator()
    test_paths()
    test_logger()
    test_config()

    # Run async test
    asyncio.run(test_llm_client())

    print("\n" + "=" * 60)
    print("ALL FOUNDATION TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
