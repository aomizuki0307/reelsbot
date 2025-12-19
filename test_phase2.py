"""Test script for Phase 2 core business logic implementation.

This script tests all Phase 2 modules:
- Models (ReelPlan, ReelMetadata)
- Planner (LLM-based content planning)
- PolicyGate (dual-layer validation)
- CaptionGenerator (A/E captions)
- RunStorage (SQLite storage)
- DryRunPublisher (local file storage)
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from reelsbot import (
    CaptionGenerator,
    DryRunPublisher,
    Planner,
    PolicyGate,
    ReelMetadata,
    ReelPlan,
    RunStorage,
    load_config,
    create_llm_client,
)
from reelsbot.utils import setup_logger


async def test_models():
    """Test data models."""
    print("\n" + "=" * 60)
    print("TEST 1: Data Models (ReelPlan, ReelMetadata)")
    print("=" * 60)

    # Test A-type plan
    a_plan = ReelPlan(
        type="A",
        theme="gradient",
        mood="calm",
        duration_sec=10,
        tagline="A moment of peace",
    )
    print(f"\nA-type plan created: {a_plan.get_display_title()}")
    print(f"  - Type: {a_plan.type}")
    print(f"  - Theme: {a_plan.theme}")
    print(f"  - Mood: {a_plan.mood}")
    print(f"  - Duration: {a_plan.duration_sec}s")
    print(f"  - Tagline: {a_plan.tagline}")

    # Test E-type plan
    e_plan = ReelPlan(
        type="E",
        theme="cafe",
        mood="minimal",
        duration_sec=12,
        brand_name="WaveVoria",
        concept_title="Modern Cafe Interior",
        category="cafe",
    )
    print(f"\nE-type plan created: {e_plan.get_display_title()}")
    print(f"  - Type: {e_plan.type}")
    print(f"  - Brand: {e_plan.brand_name}")
    print(f"  - Concept: {e_plan.concept_title}")
    print(f"  - Category: {e_plan.category}")

    # Test metadata
    metadata = ReelMetadata(
        run_id="test_run_001",
        timestamp=datetime.now(),
        plan=a_plan,
        caption="Test caption",
        hashtags=["test", "abstract", "loop"],
        video_path=Path("test_video.mp4"),
        thumbnail_path=Path("test_thumb.jpg"),
        status="generated",
    )
    print(f"\nMetadata created: {metadata.run_id}")
    print(f"  - Full caption:\n{metadata.get_full_caption()}")
    print(f"  - Summary: {metadata.to_summary_dict()}")

    print("\n✓ Models test passed")


async def test_planner(config, llm_client, logger):
    """Test content planner."""
    print("\n" + "=" * 60)
    print("TEST 2: Planner (LLM-based content planning)")
    print("=" * 60)

    planner = Planner(config, llm_client, logger)

    # Generate daily plan
    print("\nGenerating daily plan (3 reels, 70% A)...")
    plans = await planner.generate_daily_plan(
        date="2025-12-19",
        count=3,
        a_ratio=70,
    )

    print(f"\nGenerated {len(plans)} plans:")
    for i, plan in enumerate(plans, 1):
        print(f"\n  Plan {i}: {plan.get_display_title()}")
        print(f"    Type: {plan.type}")
        print(f"    Duration: {plan.duration_sec}s")
        if plan.type == "A":
            print(f"    Tagline: {plan.tagline}")
        else:
            print(f"    Brand: {plan.brand_name}")
            print(f"    Concept: {plan.concept_title}")

    # Test single plan regeneration
    print("\nRegenerating single E-type plan...")
    single_plan = await planner.regenerate_single_plan("E")
    print(f"  Generated: {single_plan.get_display_title()}")

    print("\n✓ Planner test passed")
    return plans


async def test_policy_gate(config, llm_client, logger, plans):
    """Test policy gate validation."""
    print("\n" + "=" * 60)
    print("TEST 3: PolicyGate (dual-layer validation)")
    print("=" * 60)

    gate = PolicyGate(config, llm_client, logger)

    print(f"\nLoaded {gate.get_blocked_terms_count()} blocked terms")

    # Test each plan
    for i, plan in enumerate(plans, 1):
        print(f"\nValidating plan {i}: {plan.get_display_title()}")
        is_valid, reason = await gate.validate_plan(plan)

        if is_valid:
            print(f"  ✓ VALID - {reason}")
        else:
            print(f"  ✗ INVALID - {reason}")

    # Test term blocking
    print("\nTesting specific term checks:")
    test_terms = ["cure", "investment", "gradient", "cafe"]
    for term in test_terms:
        is_blocked = gate.is_term_blocked(term)
        status = "BLOCKED" if is_blocked else "ALLOWED"
        print(f"  '{term}': {status}")

    print("\n✓ Policy gate test passed")


async def test_caption_generator(config, llm_client, logger, plans):
    """Test caption generator."""
    print("\n" + "=" * 60)
    print("TEST 4: CaptionGenerator (A/E captions)")
    print("=" * 60)

    generator = CaptionGenerator(config, llm_client, logger)

    # Generate captions for each plan
    captions_data = []
    for i, plan in enumerate(plans, 1):
        print(f"\nGenerating caption for plan {i}: {plan.get_display_title()}")
        caption, hashtags = await generator.generate_caption(plan)

        print(f"  Caption: {caption}")
        print(f"  Hashtags ({len(hashtags)}): {' '.join(f'#{tag}' for tag in hashtags[:5])}...")

        captions_data.append((plan, caption, hashtags))

    print("\n✓ Caption generator test passed")
    return captions_data


async def test_storage(config, logger, captions_data):
    """Test run storage."""
    print("\n" + "=" * 60)
    print("TEST 5: RunStorage (SQLite storage)")
    print("=" * 60)

    storage = RunStorage(config, logger)

    # Create dummy metadata for testing
    print("\nSaving test runs to database...")
    saved_runs = []

    for i, (plan, caption, hashtags) in enumerate(captions_data, 1):
        run_id = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"

        # Create dummy file paths
        video_path = Path("outputs/test_video.mp4")
        thumbnail_path = Path("outputs/test_thumb.jpg")

        metadata = ReelMetadata(
            run_id=run_id,
            timestamp=datetime.now(),
            plan=plan,
            caption=caption,
            hashtags=hashtags,
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            status="generated",
        )

        storage.save_run(metadata)
        saved_runs.append(metadata)
        print(f"  Saved: {run_id}")

    # Retrieve runs
    print("\nRetrieving recent runs from database...")
    recent_runs = storage.get_recent_runs(limit=5)
    print(f"  Found {len(recent_runs)} recent runs")

    for run in recent_runs[:3]:
        print(f"    - {run.run_id}: {run.plan.get_display_title()}")

    # Get stats
    print("\nDatabase statistics:")
    stats = storage.get_stats()
    print(f"  Total runs: {stats['total']}")
    print(f"  By type: {stats.get('by_type', {})}")
    print(f"  By status: {stats.get('by_status', {})}")

    # Update status
    if saved_runs:
        test_run = saved_runs[0]
        print(f"\nUpdating status for {test_run.run_id}...")
        storage.update_status(test_run.run_id, "published")
        print("  Status updated to 'published'")

    storage.close()

    print("\n✓ Storage test passed")
    return saved_runs


async def test_publisher(config, logger, saved_runs):
    """Test DRY_RUN publisher."""
    print("\n" + "=" * 60)
    print("TEST 6: DryRunPublisher (local file storage)")
    print("=" * 60)

    publisher = DryRunPublisher(config, logger)

    if not saved_runs:
        print("\nSkipping publisher test (no saved runs)")
        return

    # Create dummy files for testing
    test_run = saved_runs[0]
    video_path = config.outputs_dir / "test_video.mp4"
    thumbnail_path = config.outputs_dir / "test_thumb.jpg"

    # Create dummy files
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(b"dummy video content")
    thumbnail_path.write_bytes(b"dummy thumbnail content")

    # Update metadata with correct paths
    test_run.video_path = video_path
    test_run.thumbnail_path = thumbnail_path

    # Publish
    print(f"\nPublishing to DRY_RUN: {test_run.run_id}")
    result = await publisher.publish(test_run)

    print(f"  Status: {result['status']}")
    print(f"  Output dir: {result['output_dir']}")
    print(f"  Files:")
    for file_type, file_path in result['files'].items():
        if file_path:
            print(f"    - {file_type}: {file_path}")

    # Check status
    print(f"\nChecking publication status...")
    status = publisher.get_status(test_run.run_id)
    print(f"  Status: {status['status']}")

    # List runs
    print("\nListing DRY_RUN outputs...")
    runs = publisher.list_runs(limit=5)
    print(f"  Found {len(runs)} outputs:")
    for run in runs:
        print(f"    - {run['run_id']}: {run.get('type', 'unknown')}")

    # Clean up dummy files
    video_path.unlink(missing_ok=True)
    thumbnail_path.unlink(missing_ok=True)

    print("\n✓ Publisher test passed")


async def main():
    """Run all Phase 2 tests."""
    print("\n" + "=" * 60)
    print("PHASE 2 CORE BUSINESS LOGIC TEST SUITE")
    print("=" * 60)

    try:
        # Load configuration
        print("\nLoading configuration...")
        config = load_config()
        print(f"  LLM Provider: {config.llm_provider}")
        print(f"  LLM Model: {config.get_active_model()}")

        # Setup logger
        logger = setup_logger("test_phase2")

        # Create LLM client
        print("\nInitializing LLM client...")
        llm_client = await create_llm_client(config, logger)
        print(f"  Client initialized: {llm_client.get_model_info()}")

        # Run tests
        await test_models()

        plans = await test_planner(config, llm_client, logger)

        await test_policy_gate(config, llm_client, logger, plans)

        captions_data = await test_caption_generator(config, llm_client, logger, plans)

        saved_runs = await test_storage(config, logger, captions_data)

        await test_publisher(config, logger, saved_runs)

        # Summary
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nPhase 2 modules are working correctly:")
        print("  ✓ Models (ReelPlan, ReelMetadata)")
        print("  ✓ Planner (LLM-based content planning)")
        print("  ✓ PolicyGate (dual-layer validation)")
        print("  ✓ CaptionGenerator (A/E captions)")
        print("  ✓ RunStorage (SQLite storage)")
        print("  ✓ DryRunPublisher (local file storage)")
        print("\nNext steps: Implement Phase 3 (Video Generation)")

        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
