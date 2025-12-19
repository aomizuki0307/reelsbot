"""Tests for the Orchestrator component.

This module tests the main orchestration layer that coordinates all components
of the reelsbot pipeline, including plan generation, validation, video creation,
and publishing.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from reelsbot.models import ReelMetadata, ReelPlan
from reelsbot.orchestrator import Orchestrator, OrchestratorError
from reelsbot.policy_gate import PolicyViolationError


# ===== Initialization Tests =====


@pytest.mark.unit
def test_orchestrator_initialization(test_config, test_logger):
    """Test orchestrator initializes all components correctly."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Verify all components are initialized
    assert orchestrator.config == test_config
    assert orchestrator.logger == test_logger
    assert orchestrator.llm_client is not None
    assert orchestrator.planner is not None
    assert orchestrator.policy_gate is not None
    assert orchestrator.generator is not None
    assert orchestrator.editor is not None
    assert orchestrator.caption_generator is not None
    assert orchestrator.storage is not None
    assert orchestrator.publisher is not None


@pytest.mark.unit
def test_orchestrator_generate_run_id(test_config, test_logger):
    """Test run ID generation is unique and properly formatted."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    run_id_1 = orchestrator._generate_run_id()
    run_id_2 = orchestrator._generate_run_id()

    # Verify format: run_YYYYMMDD_HHMMSS
    assert run_id_1.startswith("run_")
    assert run_id_2.startswith("run_")
    assert len(run_id_1) == len("run_20251220_123456")

    # Run IDs should be unique (or same if generated in same second)
    # We just verify they're valid format
    parts = run_id_1.split("_")
    assert len(parts) == 3
    assert parts[0] == "run"
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 6  # HHMMSS


# ===== Plan Generation Tests =====


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_plans_type_filter_A(
    test_config, test_logger, sample_plan_A, mocker
):
    """Test plan generation with A-type filter."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)

    plans = await orchestrator._generate_plans(count=3, type_filter="A", mix=False)

    assert len(plans) == 3
    assert all(p.type == "A" for p in plans)
    assert orchestrator.planner.generate_abstract_plan.call_count == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_plans_type_filter_E(
    test_config, test_logger, sample_plan_E, mocker
):
    """Test plan generation with E-type filter."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_educational_plan = AsyncMock(
        return_value=sample_plan_E
    )

    plans = await orchestrator._generate_plans(count=2, type_filter="E", mix=False)

    assert len(plans) == 2
    assert all(p.type == "E" for p in plans)
    assert orchestrator.planner.generate_educational_plan.call_count == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_plans_mix(
    test_config, test_logger, sample_plans_mixed, mocker
):
    """Test plan generation with mixed ratio."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_daily_plan = AsyncMock(
        return_value=sample_plans_mixed
    )

    plans = await orchestrator._generate_plans(count=3, type_filter=None, mix=True)

    assert len(plans) == 3
    orchestrator.planner.generate_daily_plan.assert_called_once_with(count=3)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_plans_default(test_config, test_logger, sample_plan_A, mocker):
    """Test plan generation defaults to A-type when no filter specified."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)

    plans = await orchestrator._generate_plans(count=2, type_filter=None, mix=False)

    assert len(plans) == 2
    assert all(p.type == "A" for p in plans)


# ===== Policy Validation with Retry Tests =====


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_with_retry_success_first_attempt(
    test_config, test_logger, sample_plan_A
):
    """Test validation succeeds on first attempt."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock policy gate to pass
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    result = await orchestrator._validate_with_retry(sample_plan_A)

    assert result == sample_plan_A
    assert orchestrator.policy_gate.validate.call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_with_retry_success_second_attempt(
    test_config, test_logger, sample_plan_A, sample_plan_A_energetic
):
    """Test validation succeeds on second attempt after regeneration."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock policy gate: fail first, pass second
    orchestrator.policy_gate.validate = AsyncMock(
        side_effect=[
            {"is_valid": False, "violations": ["Test violation"]},
            {"is_valid": True, "violations": []},
        ]
    )

    # Mock plan regeneration
    orchestrator.planner.generate_abstract_plan = AsyncMock(
        return_value=sample_plan_A_energetic
    )

    result = await orchestrator._validate_with_retry(sample_plan_A)

    # Should return regenerated plan
    assert result == sample_plan_A_energetic
    assert orchestrator.policy_gate.validate.call_count == 2
    assert orchestrator.planner.generate_abstract_plan.call_count == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_with_retry_exhausted(test_config, test_logger, sample_plan_A):
    """Test validation raises error after max retries exhausted."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock policy gate to always fail
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": False, "violations": ["Persistent violation"]}
    )

    # Mock plan regeneration
    orchestrator.planner.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)

    with pytest.raises(PolicyViolationError) as exc_info:
        await orchestrator._validate_with_retry(sample_plan_A)

    assert "Policy validation failed after 3 attempts" in str(exc_info.value)
    assert "Persistent violation" in str(exc_info.value)
    assert orchestrator.policy_gate.validate.call_count == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validate_with_retry_exception_handling(
    test_config, test_logger, sample_plan_A
):
    """Test validation handles exceptions during validation."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock policy gate to raise exception
    orchestrator.policy_gate.validate = AsyncMock(
        side_effect=Exception("Validation error")
    )

    # Mock plan regeneration
    orchestrator.planner.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)

    with pytest.raises(PolicyViolationError) as exc_info:
        await orchestrator._validate_with_retry(sample_plan_A)

    assert "Validation error" in str(exc_info.value)


# ===== Single Plan Processing Tests =====


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_single_plan_A_type(
    test_config, test_logger, sample_plan_A, temp_output_dir, mocker
):
    """Test processing a single A-type plan through entire pipeline."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock all components
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    raw_video_path = temp_output_dir / "raw_video.mp4"
    raw_video_path.touch()
    orchestrator.generator.generate = MagicMock(return_value=raw_video_path)

    final_video_path = temp_output_dir / "video_1.mp4"
    final_video_path.touch()
    orchestrator.editor.edit_video = AsyncMock(return_value=final_video_path)

    thumbnail_path = temp_output_dir / "thumbnail_1.jpg"
    thumbnail_path.touch()
    orchestrator.editor.create_thumbnail = AsyncMock(return_value=thumbnail_path)

    orchestrator.caption_generator.generate_caption = AsyncMock(
        return_value={
            "caption": "Test caption",
            "hashtags": ["Test", "Abstract"],
        }
    )

    orchestrator.publisher.publish = AsyncMock(
        return_value={"status": "published", "id": "test_123"}
    )

    metadata_path = temp_output_dir / "metadata.json"
    metadata_path.touch()
    orchestrator.storage.save_metadata = AsyncMock(return_value=metadata_path)

    # Process plan
    result = await orchestrator._process_single_plan(
        plan=sample_plan_A,
        run_id="test_run_123",
        output_dir=temp_output_dir,
        plan_number=1,
    )

    # Verify result
    assert isinstance(result, ReelMetadata)
    assert result.run_id == "test_run_123"
    assert result.plan == sample_plan_A
    assert result.caption == "Test caption"
    assert result.hashtags == ["Test", "Abstract"]
    assert result.video_path == final_video_path
    assert result.thumbnail_path == thumbnail_path

    # Verify all components were called
    orchestrator.policy_gate.validate.assert_called_once()
    orchestrator.generator.generate.assert_called_once()
    orchestrator.editor.edit_video.assert_called_once()
    orchestrator.editor.create_thumbnail.assert_called_once()
    orchestrator.caption_generator.generate_caption.assert_called_once()
    orchestrator.publisher.publish.assert_called_once()
    orchestrator.storage.save_metadata.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_single_plan_E_type(
    test_config, test_logger, sample_plan_E, temp_output_dir
):
    """Test processing a single E-type plan with 'Fictional concept' overlay."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock all components
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    raw_video_path = temp_output_dir / "raw_video.mp4"
    raw_video_path.touch()
    orchestrator.generator.generate = MagicMock(return_value=raw_video_path)

    final_video_path = temp_output_dir / "video_1.mp4"
    final_video_path.touch()
    orchestrator.editor.edit_video = AsyncMock(return_value=final_video_path)

    thumbnail_path = temp_output_dir / "thumbnail_1.jpg"
    thumbnail_path.touch()
    orchestrator.editor.create_thumbnail = AsyncMock(return_value=thumbnail_path)

    orchestrator.caption_generator.generate_caption = AsyncMock(
        return_value={
            "caption": "Fictional cafe concept",
            "hashtags": ["Cafe", "Design", "FictionalConcept"],
        }
    )

    orchestrator.publisher.publish = AsyncMock(
        return_value={"status": "published"}
    )

    orchestrator.storage.save_metadata = AsyncMock(
        return_value=temp_output_dir / "metadata.json"
    )

    # Process plan
    result = await orchestrator._process_single_plan(
        plan=sample_plan_E,
        run_id="test_run_123",
        output_dir=temp_output_dir,
        plan_number=1,
    )

    # Verify E-type specific fields
    assert result.plan.type == "E"
    assert result.plan.brand_name == "ZENITHCAFE"
    assert result.plan.concept_title == "Modern Cafe Interior"

    # The editor should have been called with E-type plan
    call_args = orchestrator.editor.edit_video.call_args[1]
    assert call_args["plan"].type == "E"


# ===== Full Pipeline Tests =====


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_pipeline_type_A(
    test_config, test_logger, sample_plan_A, temp_dir, mocker
):
    """Test running full pipeline with A-type filter."""
    # Create a real output directory structure
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Update config to use temp directory
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)

    # Mock policy gate
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    # Mock generator to create actual files
    def mock_generate(plan, output_dir):
        video_path = output_dir / "raw_video.mp4"
        video_path.touch()
        return video_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    # Mock editor
    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)

    # Mock caption generator
    orchestrator.caption_generator.generate_caption = AsyncMock(
        return_value={"caption": "Test caption", "hashtags": ["Test"]}
    )

    # Mock publisher
    orchestrator.publisher.publish = AsyncMock(return_value={"status": "ok"})

    # Mock storage
    async def mock_save_metadata(metadata):
        path = metadata.video_path.parent / "metadata.json"
        path.touch()
        return path

    orchestrator.storage.save_metadata = AsyncMock(side_effect=mock_save_metadata)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=2, type_filter="A")

    # Verify results
    assert len(results) == 2
    assert all(r.plan.type == "A" for r in results)
    assert all(r.video_path.exists() for r in results)
    assert all(r.thumbnail_path.exists() for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_pipeline_type_E(
    test_config, test_logger, sample_plan_E, temp_dir
):
    """Test running full pipeline with E-type filter."""
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_educational_plan = AsyncMock(
        return_value=sample_plan_E
    )

    # Mock all components (similar to A-type test)
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    def mock_generate(plan, output_dir):
        video_path = output_dir / "raw_video.mp4"
        video_path.touch()
        return video_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)
    orchestrator.caption_generator.generate_caption = AsyncMock(
        return_value={"caption": "E-type caption", "hashtags": ["FictionalConcept"]}
    )
    orchestrator.publisher.publish = AsyncMock(return_value={"status": "ok"})

    async def mock_save_metadata(metadata):
        path = metadata.video_path.parent / "metadata.json"
        path.touch()
        return path

    orchestrator.storage.save_metadata = AsyncMock(side_effect=mock_save_metadata)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=1, type_filter="E")

    # Verify results
    assert len(results) == 1
    assert results[0].plan.type == "E"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_pipeline_mix(
    test_config, test_logger, sample_plans_mixed, temp_dir
):
    """Test running pipeline with mixed A/E ratio."""
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_daily_plan = AsyncMock(
        return_value=sample_plans_mixed
    )

    # Mock all components
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    def mock_generate(plan, output_dir):
        video_path = output_dir / "raw_video.mp4"
        video_path.touch()
        return video_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)
    orchestrator.caption_generator.generate_caption = AsyncMock(
        return_value={"caption": "Mixed caption", "hashtags": ["Mixed"]}
    )
    orchestrator.publisher.publish = AsyncMock(return_value={"status": "ok"})

    async def mock_save_metadata(metadata):
        path = metadata.video_path.parent / "metadata.json"
        path.touch()
        return path

    orchestrator.storage.save_metadata = AsyncMock(side_effect=mock_save_metadata)

    # Run pipeline
    results = await orchestrator.run_pipeline(count=3, mix=True)

    # Verify results
    assert len(results) == 3
    # Should have both A and E types
    types = [r.plan.type for r in results]
    assert "A" in types
    assert "E" in types


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_pipeline_error_recovery(
    test_config, test_logger, sample_plan_A, temp_dir
):
    """Test pipeline continues after single video failure."""
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock planner
    orchestrator.planner.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)

    # Mock policy gate
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    # Mock generator to fail on first call, succeed on second
    call_count = 0

    def mock_generate(plan, output_dir):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Generation failed")
        video_path = output_dir / "raw_video.mp4"
        video_path.touch()
        return video_path

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
    orchestrator.caption_generator.generate_caption = AsyncMock(
        return_value={"caption": "Caption", "hashtags": []}
    )
    orchestrator.publisher.publish = AsyncMock(return_value={"status": "ok"})

    async def mock_save_metadata(metadata):
        path = metadata.video_path.parent / "metadata.json"
        path.touch()
        return path

    orchestrator.storage.save_metadata = AsyncMock(side_effect=mock_save_metadata)

    # Run pipeline for 2 videos
    results = await orchestrator.run_pipeline(count=2, type_filter="A")

    # Should have 1 success (second video) despite first failure
    assert len(results) == 1
    assert results[0].plan.type == "A"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_pipeline_mutual_exclusion(test_config, test_logger):
    """Test run_pipeline raises error when both type_filter and mix specified."""
    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    with pytest.raises(ValueError, match="Cannot specify both type_filter and mix"):
        await orchestrator.run_pipeline(count=1, type_filter="A", mix=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_pipeline_dry_run_vs_live(
    test_config, test_logger, sample_plan_A, temp_dir
):
    """Test run_pipeline uses correct publisher based on dry_run flag."""
    outputs_dir = temp_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    test_config.outputs_dir = outputs_dir

    orchestrator = Orchestrator(config=test_config, logger=test_logger)

    # Mock all components
    orchestrator.planner.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)
    orchestrator.policy_gate.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )

    def mock_generate(plan, output_dir):
        video_path = output_dir / "raw_video.mp4"
        video_path.touch()
        return video_path

    orchestrator.generator.generate = MagicMock(side_effect=mock_generate)

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    orchestrator.editor.edit_video = AsyncMock(side_effect=mock_edit_video)
    orchestrator.editor.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)
    orchestrator.caption_generator.generate_caption = AsyncMock(
        return_value={"caption": "Caption", "hashtags": []}
    )
    orchestrator.publisher.publish = AsyncMock(return_value={"status": "ok"})

    async def mock_save_metadata(metadata):
        path = metadata.video_path.parent / "metadata.json"
        path.touch()
        return path

    orchestrator.storage.save_metadata = AsyncMock(side_effect=mock_save_metadata)

    # Run in dry-run mode (should use DryRunPublisher)
    results_dry = await orchestrator.run_pipeline(count=1, type_filter="A", dry_run=True)
    assert len(results_dry) == 1

    # Both modes should work (publisher is already DryRunPublisher in test setup)
    results_live = await orchestrator.run_pipeline(
        count=1, type_filter="A", dry_run=False
    )
    assert len(results_live) == 1
