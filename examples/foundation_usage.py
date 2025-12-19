"""Example demonstrating Phase 1 foundation layer usage.

This script shows how to use all the core foundation modules together
in a typical workflow.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reelsbot import load_config
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


async def main() -> None:
    """Demonstrate foundation layer usage."""
    print("=" * 70)
    print("REELSBOT PHASE 1 FOUNDATION - USAGE EXAMPLE")
    print("=" * 70)

    # 1. Generate a run ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"example_{timestamp}"
    print(f"\n1. Generated run_id: {run_id}")

    # 2. Setup logger
    logger = setup_logger(run_id, logs_dir=Path("logs"))
    logger.info("Foundation example started")
    print("   Logger configured with run-ID tracking")

    # 3. Load configuration
    try:
        config = load_config()
        logger.info(f"Configuration loaded: {config.llm_provider} provider")
        print(f"   Configuration loaded: {config.llm_provider}")
    except ValueError as e:
        # If .env not configured, create a test config
        logger.warning(f"Could not load .env config: {e}")
        print(f"   Warning: Using test configuration (no API key)")
        config = ReelsbotConfig(
            llm_provider="anthropic",
            anthropic_api_key="test-key-for-example",
            default_a_ratio=70,
            default_e_ratio=30,
        )

    print(f"   - Provider: {config.llm_provider}")
    print(f"   - Model: {config.get_active_model()}")
    print(f"   - A/E Ratio: {config.default_a_ratio}/{config.default_e_ratio}")
    print(f"   - Video duration: {config.default_a_duration_min}-{config.default_a_duration_max}s")

    # 4. Setup output directory
    output_dir = ensure_output_dir(run_id, config.outputs_dir)
    logger.info(f"Output directory created: {output_dir}")
    print(f"\n2. Output directory: {output_dir.absolute()}")

    # 5. Generate brand names
    print("\n3. Brand name generation:")
    generator = BrandNameGenerator(seed=42)

    single_brand = generate_brand_name(seed=123)
    print(f"   Single brand: {single_brand}")
    logger.info(f"Generated brand: {single_brand}")

    batch_brands = generator.generate_batch(5)
    print(f"   Batch of 5 brands: {batch_brands}")
    logger.info(f"Generated brand batch: {batch_brands}")

    # Validate brands
    for brand in batch_brands:
        if not generator.is_safe(brand):
            logger.warning(f"Unsafe brand detected: {brand}")

    # 6. Path handling
    print("\n4. Path utilities:")

    # Test Windows path conversion
    test_path = Path("C:\\Users\\test\\videos\\output.mp4")
    ffmpeg_path = to_ffmpeg_path(test_path)
    print(f"   Windows path: {test_path}")
    print(f"   FFmpeg path:  {ffmpeg_path}")
    logger.debug(f"Path conversion: {test_path} -> {ffmpeg_path}")

    # Generate safe filename
    unsafe_name = "My Video: Part 1 <draft>?.mp4"
    safe_name = safe_filename(unsafe_name)
    print(f"   Unsafe filename: '{unsafe_name}'")
    print(f"   Safe filename:   '{safe_name}'")
    logger.debug(f"Filename sanitized: {unsafe_name} -> {safe_name}")

    # 7. LLM Client (without actual API call)
    print("\n5. LLM Client initialization:")
    try:
        client = LLMClient(config, logger)
        model_info = client.get_model_info()
        print(f"   Provider: {model_info['provider']}")
        print(f"   Model: {model_info['model']}")
        logger.info(f"LLM client initialized: {model_info}")

        # Note: We won't actually call the API without a real key
        print("   [Skipping actual API call without valid key]")

    except Exception as e:
        logger.error(f"LLM client initialization failed: {e}")
        print(f"   Error: {e}")

    # 8. Demonstrate logging levels
    print("\n6. Logging demonstration:")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    print("   See logs directory for detailed output")

    # 9. Configuration validation
    print("\n7. Configuration validation:")
    try:
        # This would fail with invalid A/E ratio
        bad_config = ReelsbotConfig(
            anthropic_api_key="test",
            default_a_ratio=50,
            default_e_ratio=40,  # Doesn't sum to 100
        )
        bad_config.validate_config()
    except ValueError as e:
        print(f"   Validation correctly caught error: {e}")
        logger.info(f"Configuration validation working: {e}")

    # 10. Summary
    print("\n" + "=" * 70)
    print("EXAMPLE COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nRun ID: {run_id}")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Log file: logs/{datetime.now().strftime('%Y%m%d')}.log")
    print("\nAll foundation components are working correctly!")

    logger.info("Foundation example completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
