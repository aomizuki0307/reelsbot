"""Pytest fixtures for reelsbot test suite.

This module provides comprehensive fixtures for all test types:
- Configuration and logger fixtures
- Mock LLM client with canned responses
- Mock FFmpeg subprocess calls
- Sample plans and metadata
- Temporary directories for test outputs
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from reelsbot.config import ReelsbotConfig
from reelsbot.models import ReelMetadata, ReelPlan
from reelsbot.utils import setup_logger


# ===== Configuration and Logger Fixtures =====


@pytest.fixture
def test_config() -> ReelsbotConfig:
    """Provide a test configuration with safe defaults.

    Returns:
        Test ReelsbotConfig with mock API key and sensible defaults.
    """
    return ReelsbotConfig(
        openai_api_key="test-api-key-12345",
        llm_model="gpt-4",
        llm_temperature=0.7,
        default_a_ratio=70,
        default_e_ratio=30,
        policy_max_retry=3,
        video_resolution=(1080, 1920),
        video_fps=30,
    )


@pytest.fixture
def test_logger():
    """Provide a test logger instance.

    Returns:
        Logger configured for testing.
    """
    return setup_logger("test_run")


# ===== Temporary Directory Fixtures =====


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test outputs.

    Automatically cleaned up after test completion.

    Yields:
        Path to temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_output_dir(temp_dir):
    """Provide a temporary output directory structure.

    Creates a structure similar to actual run outputs:
    - run_<id>/
      - video_1.mp4
      - thumbnail_1.jpg
      - metadata_1.json

    Yields:
        Path to temporary output directory.
    """
    output_dir = temp_dir / "outputs" / "run_test_123"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir


# ===== Mock LLM Client Fixtures =====


@pytest.fixture
def mock_llm_client(mocker):
    """Provide a mocked LLM client with canned responses.

    The mock returns valid JSON responses for:
    - Plan generation (daily plans)
    - Policy validation
    - Caption generation

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock LLM client with AsyncMock generate method.
    """
    mock = mocker.MagicMock()

    # Mock async generate method
    async def mock_generate(prompt: str, **kwargs):
        # Return different responses based on prompt content
        if "daily plan" in prompt.lower() or "generate" in prompt.lower():
            # Plan generation response
            return json.dumps({
                "plans": [
                    {
                        "type": "A",
                        "theme": "gradient",
                        "mood": "calm",
                        "duration_sec": 10,
                        "tagline": "A moment of peace"
                    }
                ]
            })
        elif "policy" in prompt.lower() or "validate" in prompt.lower():
            # Policy validation response
            return json.dumps({
                "is_valid": True,
                "violations": []
            })
        elif "caption" in prompt.lower():
            # Caption generation response
            return json.dumps({
                "caption": "Transform your mindset with abstract visuals that inspire calm.",
                "hashtags": ["AbstractArt", "Minimalism", "CalmVibes"]
            })
        else:
            # Default response
            return json.dumps({"status": "ok"})

    mock.generate = AsyncMock(side_effect=mock_generate)
    return mock


@pytest.fixture
def mock_llm_client_with_policy_failure(mocker):
    """Provide a mocked LLM client that fails policy validation.

    Useful for testing retry logic.

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock LLM client that always fails policy validation.
    """
    mock = mocker.MagicMock()

    async def mock_generate_failing(prompt: str, **kwargs):
        if "policy" in prompt.lower() or "validate" in prompt.lower():
            return json.dumps({
                "is_valid": False,
                "violations": ["Contains blocked term: test"]
            })
        # Still return valid responses for other requests
        return json.dumps({"status": "ok"})

    mock.generate = AsyncMock(side_effect=mock_generate_failing)
    return mock


# ===== Mock FFmpeg Fixtures =====


@pytest.fixture
def mock_ffmpeg(mocker):
    """Mock FFmpeg subprocess calls.

    Captures FFmpeg commands without executing them.

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock for subprocess.run.
    """
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="",
        stderr=""
    )
    return mock_run


@pytest.fixture
def mock_ffmpeg_command(mocker):
    """Mock the run_ffmpeg_command utility function.

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock for run_ffmpeg_command.
    """
    return mocker.patch("reelsbot.utils.ffmpeg.run_ffmpeg_command")


# ===== Sample Plan Fixtures =====


@pytest.fixture
def sample_plan_A() -> ReelPlan:
    """Provide a sample A-type (abstract) plan.

    Returns:
        Valid A-type ReelPlan.
    """
    return ReelPlan(
        type="A",
        theme="gradient",
        mood="calm",
        duration_sec=10,
        tagline="A moment of peace",
    )


@pytest.fixture
def sample_plan_A_energetic() -> ReelPlan:
    """Provide a sample energetic A-type plan.

    Returns:
        Valid A-type ReelPlan with energetic mood.
    """
    return ReelPlan(
        type="A",
        theme="kinetic",
        mood="energetic",
        duration_sec=12,
        tagline="Embrace the chaos",
    )


@pytest.fixture
def sample_plan_E() -> ReelPlan:
    """Provide a sample E-type (educational/fictional) plan.

    Returns:
        Valid E-type ReelPlan.
    """
    return ReelPlan(
        type="E",
        theme="cafe",
        mood="calm",
        duration_sec=12,
        brand_name="ZENITHCAFE",
        concept_title="Modern Cafe Interior",
        category="cafe",
    )


@pytest.fixture
def sample_plan_E_packaging() -> ReelPlan:
    """Provide a sample E-type plan for packaging design.

    Returns:
        Valid E-type ReelPlan for packaging category.
    """
    return ReelPlan(
        type="E",
        theme="packaging",
        mood="minimal",
        duration_sec=14,
        brand_name="PUREBLOOM",
        concept_title="Organic Skincare Packaging",
        category="packaging",
    )


@pytest.fixture
def sample_plans_mixed(sample_plan_A, sample_plan_E) -> list[ReelPlan]:
    """Provide a mixed list of A and E type plans.

    Args:
        sample_plan_A: A-type plan fixture.
        sample_plan_E: E-type plan fixture.

    Returns:
        List of mixed ReelPlan objects.
    """
    return [
        sample_plan_A,
        sample_plan_E,
        ReelPlan(
            type="A",
            theme="geometric",
            mood="hypnotic",
            duration_sec=11,
            tagline="Patterns of thought",
        ),
    ]


# ===== Sample Metadata Fixtures =====


@pytest.fixture
def sample_metadata_A(sample_plan_A, temp_output_dir) -> ReelMetadata:
    """Provide sample metadata for an A-type video.

    Args:
        sample_plan_A: A-type plan fixture.
        temp_output_dir: Temporary directory fixture.

    Returns:
        Valid ReelMetadata for A-type content.
    """
    # Create dummy files
    video_path = temp_output_dir / "video_1.mp4"
    thumbnail_path = temp_output_dir / "thumbnail_1.jpg"
    video_path.touch()
    thumbnail_path.touch()

    return ReelMetadata(
        run_id="run_test_123",
        timestamp=datetime.now(),
        plan=sample_plan_A,
        caption="Transform your mindset with abstract visuals.",
        hashtags=["AbstractArt", "Minimalism", "CalmVibes"],
        video_path=video_path,
        thumbnail_path=thumbnail_path,
        status="generated",
    )


@pytest.fixture
def sample_metadata_E(sample_plan_E, temp_output_dir) -> ReelMetadata:
    """Provide sample metadata for an E-type video.

    Args:
        sample_plan_E: E-type plan fixture.
        temp_output_dir: Temporary directory fixture.

    Returns:
        Valid ReelMetadata for E-type content.
    """
    # Create dummy files
    video_path = temp_output_dir / "video_1.mp4"
    thumbnail_path = temp_output_dir / "thumbnail_1.jpg"
    video_path.touch()
    thumbnail_path.touch()

    return ReelMetadata(
        run_id="run_test_123",
        timestamp=datetime.now(),
        plan=sample_plan_E,
        caption="ZENITHCAFE - Where modern design meets coffee culture.",
        hashtags=["CafeDesign", "InteriorDesign", "FictionalConcept"],
        video_path=video_path,
        thumbnail_path=thumbnail_path,
        status="generated",
    )


# ===== Mock Component Fixtures =====


@pytest.fixture
def mock_planner(mocker, sample_plan_A):
    """Provide a mocked Planner.

    Args:
        mocker: pytest-mock fixture.
        sample_plan_A: Sample plan fixture.

    Returns:
        MagicMock Planner.
    """
    mock = mocker.MagicMock()
    mock.generate_daily_plan = AsyncMock(return_value=[sample_plan_A])
    mock.generate_abstract_plan = AsyncMock(return_value=sample_plan_A)
    mock.generate_educational_plan = AsyncMock(
        return_value=ReelPlan(
            type="E",
            theme="cafe",
            mood="calm",
            duration_sec=12,
            brand_name="TESTCAFE",
            concept_title="Test Cafe",
            category="cafe",
        )
    )
    return mock


@pytest.fixture
def mock_policy_gate(mocker):
    """Provide a mocked PolicyGate that always passes.

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock PolicyGate.
    """
    mock = mocker.MagicMock()
    mock.validate = AsyncMock(return_value={
        "is_valid": True,
        "violations": []
    })
    return mock


@pytest.fixture
def mock_policy_gate_failing(mocker):
    """Provide a mocked PolicyGate that always fails.

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock PolicyGate that fails validation.
    """
    mock = mocker.MagicMock()
    mock.validate = AsyncMock(return_value={
        "is_valid": False,
        "violations": ["Test violation"]
    })
    return mock


@pytest.fixture
def mock_generator(mocker, temp_output_dir):
    """Provide a mocked video generator.

    Args:
        mocker: pytest-mock fixture.
        temp_output_dir: Temporary directory fixture.

    Returns:
        MagicMock generator.
    """
    mock = mocker.MagicMock()

    def mock_generate(plan, output_dir):
        video_path = output_dir / "raw_video.mp4"
        video_path.touch()
        return video_path

    mock.generate = mock_generate
    return mock


@pytest.fixture
def mock_editor(mocker, temp_output_dir):
    """Provide a mocked video editor.

    Args:
        mocker: pytest-mock fixture.
        temp_output_dir: Temporary directory fixture.

    Returns:
        MagicMock editor.
    """
    mock = mocker.MagicMock()

    async def mock_edit_video(plan, input_path, output_path):
        output_path.touch()
        return output_path

    async def mock_create_thumbnail(video_path, output_path, timestamp=1.0):
        output_path.touch()
        return output_path

    mock.edit_video = AsyncMock(side_effect=mock_edit_video)
    mock.create_thumbnail = AsyncMock(side_effect=mock_create_thumbnail)
    return mock


@pytest.fixture
def mock_caption_generator(mocker):
    """Provide a mocked caption generator.

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock caption generator.
    """
    mock = mocker.MagicMock()
    mock.generate_caption = AsyncMock(return_value={
        "caption": "Test caption for Instagram.",
        "hashtags": ["Test", "Automation", "Reels"]
    })
    return mock


@pytest.fixture
def mock_storage(mocker, temp_output_dir):
    """Provide a mocked storage system.

    Args:
        mocker: pytest-mock fixture.
        temp_output_dir: Temporary directory fixture.

    Returns:
        MagicMock storage.
    """
    mock = mocker.MagicMock()

    async def mock_save_metadata(metadata):
        metadata_path = temp_output_dir / f"metadata_{metadata.run_id}.json"
        metadata_path.touch()
        return metadata_path

    mock.save_metadata = AsyncMock(side_effect=mock_save_metadata)
    return mock


@pytest.fixture
def mock_publisher(mocker):
    """Provide a mocked publisher.

    Args:
        mocker: pytest-mock fixture.

    Returns:
        MagicMock publisher.
    """
    mock = mocker.MagicMock()
    mock.publish = AsyncMock(return_value={"status": "published", "id": "test_123"})
    return mock


# ===== Async Helper Fixtures =====


@pytest.fixture
async def async_temp_dir() -> AsyncIterator[Path]:
    """Provide an async temporary directory.

    Yields:
        Path to temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
