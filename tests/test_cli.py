"""Tests for the CLI interface.

This module tests all CLI commands using Click's CliRunner to ensure
proper command-line behavior, option parsing, and error handling.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from reelsbot import __version__
from reelsbot.cli import cli
from reelsbot.models import ReelMetadata, ReelPlan


@pytest.fixture
def cli_runner():
    """Provide a Click CLI test runner.

    Returns:
        CliRunner instance for testing CLI commands.
    """
    return CliRunner()


@pytest.fixture
def temp_metadata_file(temp_dir, sample_metadata_A):
    """Create a temporary metadata JSON file for testing.

    Args:
        temp_dir: Temporary directory fixture.
        sample_metadata_A: Sample metadata fixture.

    Returns:
        Path to temporary metadata file.
    """
    metadata_path = temp_dir / "metadata_test.json"

    # Convert metadata to JSON-serializable dict
    metadata_dict = sample_metadata_A.model_dump()
    metadata_dict["video_path"] = str(metadata_dict["video_path"])
    metadata_dict["thumbnail_path"] = str(metadata_dict["thumbnail_path"])
    metadata_dict["timestamp"] = metadata_dict["timestamp"].isoformat()

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_dict, f, indent=2)

    return metadata_path


# ===== Help and Version Tests =====


@pytest.mark.unit
def test_cli_help(cli_runner):
    """Test --help shows all available commands."""
    result = cli_runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Reelsbot" in result.output
    assert "Instagram Reels automation tool" in result.output
    assert "plan" in result.output
    assert "run" in result.output
    assert "validate" in result.output
    assert "info" in result.output


@pytest.mark.unit
def test_cli_version(cli_runner):
    """Test --version shows correct version."""
    result = cli_runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output
    assert "reelsbot" in result.output.lower()


# ===== Info Command Tests =====


@pytest.mark.unit
def test_cli_info_success(cli_runner, test_config, mocker):
    """Test info command shows configuration details."""
    # Mock load_config to return test config
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)

    result = cli_runner.invoke(cli, ["info"])

    assert result.exit_code == 0
    assert "System Information" in result.output
    assert "Configuration:" in result.output
    assert __version__ in result.output
    assert test_config.llm_provider in result.output
    assert str(test_config.video_resolution[0]) in result.output


@pytest.mark.unit
def test_cli_info_config_error(cli_runner, mocker):
    """Test info command handles config loading errors gracefully."""
    # Mock load_config to raise an exception
    mocker.patch("reelsbot.cli.load_config", side_effect=Exception("Config error"))

    result = cli_runner.invoke(cli, ["info"])

    assert result.exit_code == 1
    assert "Failed to load configuration" in result.output
    assert "Config error" in result.output


# ===== Plan Command Tests =====


@pytest.mark.unit
@pytest.mark.asyncio
def test_cli_plan_default(cli_runner, test_config, mock_llm_client, sample_plan_A, mocker):
    """Test plan command with default parameters."""
    # Mock dependencies
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock planner
    mock_planner_class = mocker.patch("reelsbot.cli.Planner")
    mock_planner_instance = MagicMock()
    mock_planner_instance.generate_daily_plan = AsyncMock(return_value=[sample_plan_A])
    mock_planner_class.return_value = mock_planner_instance

    result = cli_runner.invoke(cli, ["plan"])

    assert result.exit_code == 0
    assert "Content Planning" in result.output
    assert "Generated Content Plan:" in result.output
    assert "[A]" in result.output
    assert sample_plan_A.tagline in result.output


@pytest.mark.unit
@pytest.mark.asyncio
def test_cli_plan_with_count_and_ratio(
    cli_runner, test_config, mock_llm_client, sample_plan_A, mocker
):
    """Test plan command with custom count and ratio."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock planner
    mock_planner_class = mocker.patch("reelsbot.cli.Planner")
    mock_planner_instance = MagicMock()
    mock_planner_instance.generate_daily_plan = AsyncMock(
        return_value=[sample_plan_A, sample_plan_A, sample_plan_A]
    )
    mock_planner_class.return_value = mock_planner_instance

    result = cli_runner.invoke(cli, ["plan", "--count", "3", "--ratio", "60:40"])

    assert result.exit_code == 0
    assert "60% Abstract, 40% Educational" in result.output
    assert "3 posts" in result.output


@pytest.mark.unit
def test_cli_plan_invalid_ratio(cli_runner, test_config, mocker):
    """Test plan command with invalid ratio format."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)

    result = cli_runner.invoke(cli, ["plan", "--ratio", "50:40"])

    assert result.exit_code == 1
    assert "Invalid ratio" in result.output
    assert "must sum to 100" in result.output


@pytest.mark.unit
def test_cli_plan_invalid_date(cli_runner, test_config, mocker):
    """Test plan command with invalid date format."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)

    result = cli_runner.invoke(cli, ["plan", "--date", "2025-13-45"])

    assert result.exit_code == 1
    assert "Invalid date format" in result.output


@pytest.mark.unit
@pytest.mark.asyncio
def test_cli_plan_with_output_file(
    cli_runner, test_config, mock_llm_client, sample_plan_A, temp_dir, mocker
):
    """Test plan command saves to output file."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock planner
    mock_planner_class = mocker.patch("reelsbot.cli.Planner")
    mock_planner_instance = MagicMock()
    mock_planner_instance.generate_daily_plan = AsyncMock(return_value=[sample_plan_A])
    mock_planner_class.return_value = mock_planner_instance

    output_file = temp_dir / "plan.json"

    result = cli_runner.invoke(cli, ["plan", "--output", str(output_file)])

    assert result.exit_code == 0
    assert "Plan saved to:" in result.output
    assert output_file.exists()

    # Verify file contents
    with open(output_file, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    assert "plans" in plan_data
    assert len(plan_data["plans"]) == 1


# ===== Run Command Tests =====


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_run_type_A(
    cli_runner, test_config, mock_llm_client, sample_metadata_A, mocker
):
    """Test run command generates A-type video."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock orchestrator
    mock_orchestrator_class = mocker.patch("reelsbot.cli.Orchestrator")
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.run_pipeline = AsyncMock(
        return_value=[sample_metadata_A]
    )
    mock_orchestrator_class.return_value = mock_orchestrator_instance

    result = cli_runner.invoke(cli, ["run", "--count", "1", "--type", "A"])

    assert result.exit_code == 0
    assert "Video Generation" in result.output
    assert "Abstract" in result.output
    assert "Complete!" in result.output
    assert "1 video(s) generated" in result.output

    # Verify orchestrator was called correctly
    mock_orchestrator_instance.run_pipeline.assert_called_once()
    call_args = mock_orchestrator_instance.run_pipeline.call_args[1]
    assert call_args["count"] == 1
    assert call_args["type_filter"] == "A"
    assert call_args["dry_run"] is True


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_run_type_E(
    cli_runner, test_config, mock_llm_client, sample_metadata_E, mocker
):
    """Test run command generates E-type video."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock orchestrator
    mock_orchestrator_class = mocker.patch("reelsbot.cli.Orchestrator")
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.run_pipeline = AsyncMock(
        return_value=[sample_metadata_E]
    )
    mock_orchestrator_class.return_value = mock_orchestrator_instance

    result = cli_runner.invoke(cli, ["run", "--count", "1", "--type", "E"])

    assert result.exit_code == 0
    assert "Educational" in result.output
    assert "Complete!" in result.output

    # Verify orchestrator was called correctly
    call_args = mock_orchestrator_instance.run_pipeline.call_args[1]
    assert call_args["type_filter"] == "E"


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_run_mix(
    cli_runner, test_config, mock_llm_client, sample_metadata_A, mocker
):
    """Test run command with --mix generates mixed ratio."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock orchestrator
    mock_orchestrator_class = mocker.patch("reelsbot.cli.Orchestrator")
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.run_pipeline = AsyncMock(
        return_value=[sample_metadata_A, sample_metadata_A, sample_metadata_A]
    )
    mock_orchestrator_class.return_value = mock_orchestrator_instance

    result = cli_runner.invoke(cli, ["run", "--count", "3", "--mix"])

    assert result.exit_code == 0
    assert "70:30" in result.output  # Default ratio from test_config
    assert "3 video(s)" in result.output

    # Verify orchestrator was called correctly
    call_args = mock_orchestrator_instance.run_pipeline.call_args[1]
    assert call_args["count"] == 3
    assert call_args["mix"] is True


@pytest.mark.unit
def test_cli_run_mutual_exclusion(cli_runner):
    """Test --type and --mix are mutually exclusive."""
    result = cli_runner.invoke(cli, ["run", "--type", "A", "--mix"])

    assert result.exit_code == 1
    assert "Cannot specify both --type and --mix" in result.output


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_run_live_mode(
    cli_runner, test_config, mock_llm_client, sample_metadata_A, mocker
):
    """Test run command with --live mode."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock orchestrator
    mock_orchestrator_class = mocker.patch("reelsbot.cli.Orchestrator")
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.run_pipeline = AsyncMock(
        return_value=[sample_metadata_A]
    )
    mock_orchestrator_class.return_value = mock_orchestrator_instance

    result = cli_runner.invoke(cli, ["run", "--count", "1", "--type", "A", "--live"])

    assert result.exit_code == 0
    assert "LIVE" in result.output

    # Verify dry_run is False
    call_args = mock_orchestrator_instance.run_pipeline.call_args[1]
    assert call_args["dry_run"] is False


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_run_no_videos_generated(
    cli_runner, test_config, mock_llm_client, mocker
):
    """Test run command handles no videos generated."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock orchestrator to return empty list
    mock_orchestrator_class = mocker.patch("reelsbot.cli.Orchestrator")
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.run_pipeline = AsyncMock(return_value=[])
    mock_orchestrator_class.return_value = mock_orchestrator_instance

    result = cli_runner.invoke(cli, ["run", "--count", "1", "--type", "A"])

    assert result.exit_code == 0
    assert "No videos were generated successfully" in result.output


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_run_keyboard_interrupt(
    cli_runner, test_config, mock_llm_client, mocker
):
    """Test run command handles keyboard interrupt."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock orchestrator to raise KeyboardInterrupt
    mock_orchestrator_class = mocker.patch("reelsbot.cli.Orchestrator")
    mock_orchestrator_instance = MagicMock()
    mock_orchestrator_instance.run_pipeline = AsyncMock(
        side_effect=KeyboardInterrupt()
    )
    mock_orchestrator_class.return_value = mock_orchestrator_instance

    result = cli_runner.invoke(cli, ["run", "--count", "1", "--type", "A"])

    assert result.exit_code == 130
    assert "Operation cancelled by user" in result.output


# ===== Validate Command Tests =====


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_validate_success(
    cli_runner, test_config, mock_llm_client, temp_metadata_file, mocker
):
    """Test validate command with valid metadata."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock policy gate
    mock_policy_class = mocker.patch("reelsbot.cli.PolicyGate")
    mock_policy_instance = MagicMock()
    mock_policy_instance.validate = AsyncMock(
        return_value={"is_valid": True, "violations": []}
    )
    mock_policy_class.return_value = mock_policy_instance

    result = cli_runner.invoke(cli, ["validate", str(temp_metadata_file)])

    assert result.exit_code == 0
    assert "Metadata Validation" in result.output
    assert "Validation PASSED" in result.output
    assert "Content meets all policy requirements" in result.output


@pytest.mark.integration
@pytest.mark.asyncio
def test_cli_validate_failure(
    cli_runner, test_config, mock_llm_client, temp_metadata_file, mocker
):
    """Test validate command with policy violations."""
    mocker.patch("reelsbot.cli.load_config", return_value=test_config)
    mocker.patch("reelsbot.cli.create_llm_client", return_value=mock_llm_client)
    mocker.patch("reelsbot.cli.setup_logger", return_value=MagicMock())

    # Mock policy gate to fail
    mock_policy_class = mocker.patch("reelsbot.cli.PolicyGate")
    mock_policy_instance = MagicMock()
    mock_policy_instance.validate = AsyncMock(
        return_value={
            "is_valid": False,
            "violations": ["Contains blocked term", "Inappropriate content"],
        }
    )
    mock_policy_class.return_value = mock_policy_instance

    result = cli_runner.invoke(cli, ["validate", str(temp_metadata_file)])

    assert result.exit_code == 1
    assert "Validation FAILED" in result.output
    assert "Policy Violations:" in result.output
    assert "Contains blocked term" in result.output
    assert "Inappropriate content" in result.output


@pytest.mark.unit
def test_cli_validate_file_not_found(cli_runner):
    """Test validate command with non-existent file."""
    result = cli_runner.invoke(cli, ["validate", "/nonexistent/metadata.json"])

    assert result.exit_code == 2  # Click's file not found error


@pytest.mark.unit
def test_cli_validate_invalid_json(cli_runner, temp_dir):
    """Test validate command with invalid JSON file."""
    invalid_file = temp_dir / "invalid.json"
    invalid_file.write_text("not valid json {{{")

    result = cli_runner.invoke(cli, ["validate", str(invalid_file)])

    assert result.exit_code == 1
    assert "Invalid JSON" in result.output
