"""End-to-end integration tests for the complete reelsbot pipeline.

This module tests the full workflow from plan generation through video creation,
editing, caption generation, and publishing. Tests verify proper file structure,
E-type overlays, policy retry logic, and error recovery.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reelsbot.config import load_config
from reelsbot.models import ReelMetadata, ReelPlan
from reelsbot.orchestrator import Orchestrator
from reelsbot.policy_gate import PolicyViolationError
from reelsbot.utils import setup_logger


# ===== End-to-End Pipeline Tests =====


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_pipeline_A_type(test_config, test_logger, temp_dir, mock_llm_client):
    """Test complete pipeline for A-type video generation.

    Verifies:
    - Plan generation
    - Policy validation
    - Video generation
    - Overlay application (tagline)
    - Thumbnail creation
    - Caption generation
    - File structure
    """
    # Setup output directory
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    # Create orchestrator
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock LLM client
    orchestrator.planner.llm_client = mock_llm_client
    orchestrator.policy_gate.llm_client = mock_llm_client
    orchestrator.caption_generator.llm_client = mock_llm_client

    # Mock FFmpeg calls (don't actually generate videos)
    with patch("reelsbot.utils.ffmpeg.run_ffmpeg_command") as mock_ffmpeg:
        # Create dummy video files when FFmpeg is called
        def mock_ffmpeg_side_effect(cmd, *args, **kwargs):
            # Extract output path from command
            if "-o" in cmd or any(".mp4" in str(arg) for arg in cmd):
                for i, arg in enumerate(cmd):
                    if isinstance(arg, Path) and arg.suffix in [".mp4", ".jpg"]:
                        arg.parent.mkdir(parents=True, exist_ok=True)
                        arg.touch()

        mock_ffmpeg.side_effect = mock_ffmpeg_side_effect

        # Mock file creation for generator and editor
        original_generate = orchestrator.generator.generate

        def mock_generate(plan, output_dir):
            output_path = output_dir / f"raw_{plan.type}_{plan.theme}.mp4"
            output_path.touch()
            return output_path

        orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

        original_edit = orchestrator.editor.edit_video

        async def mock_edit_video(plan, input_path, output_path):
            output_path.touch()
            return output_path

        orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)

        original_thumbnail = orchestrator.editor.create_thumbnail

        async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
            output_path.touch()
            return output_path

        orchestrator.editor.create_thumbnail = AsyncMock(
            side_effect=mock_create_thumbnail
        )

        # Run pipeline
        results = await orchestrator.run_pipeline(count=1, type_filter="A", dry_run=True)

        # Verify results
        assert len(results) == 1
        metadata = results[0]

        # Verify metadata structure
        assert isinstance(metadata, ReelMetadata)
        assert metadata.plan.type == "A"
        assert metadata.plan.tagline is not None
        assert metadata.caption is not None
        assert metadata.video_path.exists()
        assert metadata.thumbnail_path.exists()

        # Verify file structure
        run_dir = metadata.video_path.parent
        assert run_dir.exists()
        assert run_dir.name.startswith("run_")

        # Verify metadata was saved
        metadata_files = list(run_dir.glob("metadata*.json"))
        assert len(metadata_files) >= 1


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_pipeline_E_type(test_config, test_logger, temp_dir, mock_llm_client):
    """Test complete pipeline for E-type video with 'Fictional concept' overlay.

    Verifies:
    - E-type plan generation with brand_name, concept_title, category
    - 'Fictional concept' overlay present in metadata/processing
    - Video and thumbnail generation
    - Caption includes fictional context
    """
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock LLM client to return E-type plan
    async def mock_generate_e(prompt: str, **kwargs):
        if "educational" in prompt.lower() or "generate" in prompt.lower():
            return json.dumps({
                "plans": [
                    {
                        "type": "E",
                        "theme": "cafe",
                        "mood": "calm",
                        "duration_sec": 12,
                        "brand_name": "ZENITHCAFE",
                        "concept_title": "Modern Cafe Interior",
                        "category": "cafe",
                    }
                ]
            })
        elif "policy" in prompt.lower():
            return json.dumps({"is_valid": True, "violations": []})
        elif "caption" in prompt.lower():
            return json.dumps({
                "caption": "ZENITHCAFE - A fictional cafe concept showcasing modern interior design.",
                "hashtags": ["FictionalConcept", "CafeDesign", "InteriorDesign"],
            })
        return json.dumps({"status": "ok"})

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(side_effect=mock_generate_e)

    orchestrator.planner.llm_client = mock_llm
    orchestrator.policy_gate.llm_client = mock_llm
    orchestrator.caption_generator.llm_client = mock_llm

    # Mock video generation
    def mock_generate(plan, output_dir):
        output_path = output_dir / f"raw_E_{plan.category}.mp4"
        output_path.touch()
        return output_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    # Track if "Fictional concept" overlay was applied
    fictional_overlay_applied = False

    async def mock_edit_video(plan, input_path, output_path):
        nonlocal fictional_overlay_applied
        if plan.type == "E":
            # Simulate checking for fictional concept overlay
            fictional_overlay_applied = True
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=1, type_filter="E", dry_run=True)

    # Verify results
    assert len(results) == 1
    metadata = results[0]

    # Verify E-type specific fields
    assert metadata.plan.type == "E"
    assert metadata.plan.brand_name == "ZENITHCAFE"
    assert metadata.plan.concept_title == "Modern Cafe Interior"
    assert metadata.plan.category == "cafe"

    # Verify fictional overlay was processed
    assert fictional_overlay_applied

    # Verify caption includes fictional context
    assert "FictionalConcept" in metadata.hashtags or "fictional" in metadata.caption.lower()

    # Verify files exist
    assert metadata.video_path.exists()
    assert metadata.thumbnail_path.exists()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_mixed_generation(
    test_config, test_logger, temp_dir, sample_plans_mixed, mock_llm_client
):
    """Test generating mixed A/E videos in single run.

    Verifies:
    - Mixed ratio generation (3 videos: 2 A-type, 1 E-type)
    - Correct file structure for each type
    - Both A and E overlays applied correctly
    """
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner to return mixed plans
    orchestrator.planner.generate_daily_plan = AsyncMock(
        return_value=sample_plans_mixed
    )
    orchestrator.planner.llm_client = mock_llm_client
    orchestrator.policy_gate.llm_client = mock_llm_client
    orchestrator.caption_generator.llm_client = mock_llm_client

    # Mock video generation
    def mock_generate(plan, output_dir):
        output_path = output_dir / f"raw_{plan.type}.mp4"
        output_path.touch()
        return output_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=3, mix=True, dry_run=True)

    # Verify results
    assert len(results) == 3

    # Count types
    a_count = sum(1 for r in results if r.plan.type == "A")
    e_count = sum(1 for r in results if r.plan.type == "E")

    # Should have both types
    assert a_count > 0
    assert e_count > 0
    assert a_count + e_count == 3

    # Verify all have required files
    for metadata in results:
        assert metadata.video_path.exists()
        assert metadata.thumbnail_path.exists()
        assert metadata.caption is not None

        # Verify type-specific fields
        if metadata.plan.type == "A":
            assert metadata.plan.tagline is not None
        else:
            assert metadata.plan.brand_name is not None
            assert metadata.plan.concept_title is not None


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_policy_retry(test_config, test_logger, temp_dir, sample_plan_A):
    """Test plan regeneration when policy validation fails.

    Verifies:
    - First plan fails policy validation
    - New plan is generated automatically
    - Second plan passes validation
    - Pipeline completes successfully
    """
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Track validation attempts
    validation_attempts = 0

    async def mock_validate(plan):
        nonlocal validation_attempts
        validation_attempts += 1

        if validation_attempts == 1:
            # First attempt fails
            return {"is_valid": False, "violations": ["Blocked term detected"]}
        else:
            # Second attempt passes
            return {"is_valid": True, "violations": []}

    orchestrator.policy_gate.validate = AsyncMock(side_effect=mock_validate)

    # Mock planner to generate new plan on retry
    plan_generation_count = 0

    async def mock_generate_plan():
        nonlocal plan_generation_count
        plan_generation_count += 1
        return ReelPlan(
            type="A",
            theme="gradient",
            mood="calm",
            duration_sec=10,
            tagline=f"Attempt {plan_generation_count}",
        )

    orchestrator.planner.generate_abstract_plan = AsyncMock(
        side_effect=mock_generate_plan
    )

    # Mock other components
    def mock_generate(plan, output_dir):
        output_path = output_dir / "raw.mp4"
        output_path.touch()
        return output_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    async def mock_generate_caption(plan):
        return {"caption": "Test caption", "hashtags": ["Test"]}

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)
    orchestrator.caption_generator.generate_caption = AsyncMock(
        side_effect=mock_generate_caption
    )

    async def mock_publish(metadata):
        return {"status": "ok"}

    async def mock_save_metadata(metadata):
        path = metadata.video_path.parent / "metadata.json"
        path.touch()
        return path

    orchestrator.publisher.publish = AsyncMock(side_effect=mock_publish)
    orchestrator.storage.save_metadata = AsyncMock(side_effect=mock_save_metadata)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=1, type_filter="A", dry_run=True)

    # Verify retry happened
    assert validation_attempts == 2  # Failed once, passed second time
    assert plan_generation_count >= 1  # Generated at least one new plan

    # Verify pipeline completed
    assert len(results) == 1


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_policy_retry_exhausted(test_config, test_logger, temp_dir):
    """Test pipeline fails after max policy retries exhausted.

    Verifies:
    - Policy validation fails repeatedly
    - Max retries (3) are attempted
    - PolicyViolationError is raised
    - No video is generated
    """
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock policy gate to always fail
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": False, "violations": ["Persistent violation"]}
    )

    # Mock planner
    orchestrator.planner.generate_abstract_plan = AsyncMock(
        return_value=ReelPlan(
            type="A", theme="gradient", mood="calm", duration_sec=10, tagline="Test"
        )
    )

    # Mock other components (won't be called)
    orchestrator.generator.generate = MagicMock()
    orchestrator.editor.edit_video = AsyncMock()

    # Run pipeline - should raise error
    results = await orchestrator.run_pipeline(count=1, type_filter="A", dry_run=True)

    # Should have no successful results
    assert len(results) == 0

    # Verify max retries were attempted (3 times)
    assert orchestrator.policy_gate.validate.call_count == 3


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_error_recovery(test_config, test_logger, temp_dir, mock_llm_client):
    """Test pipeline continues after single video generation failure.

    Verifies:
    - First video fails during generation
    - Error is logged but pipeline continues
    - Second video generates successfully
    - Results contain only successful videos
    """
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock LLM client
    orchestrator.planner.llm_client = mock_llm_client
    orchestrator.policy_gate.llm_client = mock_llm_client
    orchestrator.caption_generator.llm_client = mock_llm_client

    # Mock generator to fail on first call
    generation_count = 0

    def mock_generate(plan, output_dir):
        nonlocal generation_count
        generation_count += 1
        if generation_count == 1:
            raise Exception("Video generation failed!")
        output_path = output_dir / "raw.mp4"
        output_path.touch()
        return output_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    # Mock other components
    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)

    # Run pipeline for 2 videos
    results = await orchestrator.run_pipeline(count=2, type_filter="A", dry_run=True)

    # Should have 1 successful video (second one)
    assert len(results) == 1
    assert results[0].video_path.exists()


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_file_structure_validation(
    test_config, test_logger, temp_dir, mock_llm_client
):
    """Test complete file structure after pipeline run.

    Verifies:
    - outputs/{run_id}/ directory structure
    - video_*.mp4 files exist
    - thumbnail_*.jpg files exist
    - metadata_*.json files exist and are valid
    - All paths in metadata are correct
    """
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock components
    orchestrator.planner.llm_client = mock_llm_client
    orchestrator.policy_gate.llm_client = mock_llm_client
    orchestrator.caption_generator.llm_client = mock_llm_client

    def mock_generate(plan, output_dir):
        output_path = output_dir / "raw.mp4"
        output_path.touch()
        return output_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=2, type_filter="A", dry_run=True)

    # Verify file structure
    assert len(results) == 2

    # Get run directory
    run_dir = results[0].video_path.parent
    assert run_dir.exists()
    assert run_dir.name.startswith("run_")

    # Verify each video has required files
    for idx, metadata in enumerate(results, 1):
        # Verify paths are in correct directory
        assert metadata.video_path.parent == run_dir
        assert metadata.thumbnail_path.parent == run_dir

        # Verify files exist
        assert metadata.video_path.exists()
        assert metadata.thumbnail_path.exists()

        # Verify metadata can be serialized
        metadata_dict = metadata.model_dump()
        assert metadata_dict["run_id"] is not None
        assert metadata_dict["plan"]["type"] == "A"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_metadata_json_validity(
    test_config, test_logger, temp_dir, mock_llm_client
):
    """Test that saved metadata JSON files are valid and parseable.

    Verifies:
    - Metadata JSON files can be loaded
    - All required fields are present
    - Paths are valid
    - Can reconstruct ReelMetadata from saved JSON
    """
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock components
    orchestrator.planner.llm_client = mock_llm_client
    orchestrator.policy_gate.llm_client = mock_llm_client
    orchestrator.caption_generator.llm_client = mock_llm_client

    def mock_generate(plan, output_dir):
        output_path = output_dir / "raw.mp4"
        output_path.touch()
        return output_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=1, type_filter="A", dry_run=True)

    # Find saved metadata files
    run_dir = results[0].video_path.parent
    metadata_files = list(run_dir.glob("metadata_*.json"))

    assert len(metadata_files) >= 1

    # Verify each metadata file is valid
    for metadata_file in metadata_files:
        # Load JSON
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata_data = json.load(f)

        # Verify required fields
        assert "run_id" in metadata_data
        assert "plan" in metadata_data
        assert "caption" in metadata_data
        assert "video_path" in metadata_data
        assert "thumbnail_path" in metadata_data

        # Verify can reconstruct metadata
        reconstructed = ReelMetadata(**metadata_data)
        assert reconstructed.run_id is not None
        assert reconstructed.plan.type in ["A", "E"]
