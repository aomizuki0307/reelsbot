"""Tests for configuration module."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from reelsbot.config import ReelsbotConfig, load_config


class TestReelsbotConfig:
    """Tests for ReelsbotConfig class."""

    def test_default_values(self) -> None:
        """Test that default configuration values are set correctly."""
        config = ReelsbotConfig(
            openai_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )

        assert config.llm_provider == "openai"
        assert config.llm_temperature == 0.7
        assert config.llm_max_tokens == 2000
        assert config.default_a_duration_min == 8
        assert config.default_a_duration_max == 12
        assert config.video_resolution == (1080, 1920)
        assert config.video_fps == 30

    def test_llm_provider_validation(self) -> None:
        """Test LLM provider must be anthropic or openai."""
        # Valid providers
        config1 = ReelsbotConfig(
            llm_provider="anthropic",
            anthropic_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )
        assert config1.llm_provider == "anthropic"

        config2 = ReelsbotConfig(
            llm_provider="openai",
            openai_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )
        assert config2.llm_provider == "openai"

    def test_temperature_bounds(self) -> None:
        """Test temperature must be between 0 and 2."""
        # Valid temperature
        config = ReelsbotConfig(
            llm_temperature=1.5,
            anthropic_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )
        assert config.llm_temperature == 1.5

        # Invalid temperature - too high
        with pytest.raises(ValidationError):
            ReelsbotConfig(
                llm_temperature=3.0,
                anthropic_api_key="test-key",
                default_a_ratio=70,
                default_e_ratio=30,
            )

        # Invalid temperature - negative
        with pytest.raises(ValidationError):
            ReelsbotConfig(
                llm_temperature=-0.5,
                anthropic_api_key="test-key",
                default_a_ratio=70,
                default_e_ratio=30,
            )

    def test_duration_validation(self) -> None:
        """Test video duration validation."""
        config = ReelsbotConfig(
            default_a_duration_min=8,
            default_a_duration_max=12,
            default_e_duration_min=10,
            default_e_duration_max=14,
            anthropic_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )

        # Validate after creation
        with pytest.raises(ValueError, match="cannot be greater than"):
            bad_config = ReelsbotConfig(
                default_a_duration_min=15,
                default_a_duration_max=10,
                anthropic_api_key="test-key",
                default_a_ratio=70,
                default_e_ratio=30,
            )
            bad_config.validate_config()

    def test_ae_ratio_validation(self) -> None:
        """Test A/E ratio must sum to 100."""
        # Valid ratio
        config = ReelsbotConfig(
            default_a_ratio=60,
            default_e_ratio=40,
            anthropic_api_key="test-key",
        )
        config.validate_config()

        # Invalid ratio - doesn't sum to 100
        with pytest.raises(ValueError, match="must sum to 100"):
            bad_config = ReelsbotConfig(
                default_a_ratio=60,
                default_e_ratio=30,
                anthropic_api_key="test-key",
            )
            bad_config.validate_config()

    def test_get_active_api_key_anthropic(self) -> None:
        """Test getting API key for Anthropic provider."""
        config = ReelsbotConfig(
            llm_provider="anthropic",
            anthropic_api_key="test-anthropic-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )

        api_key = config.get_active_api_key()
        assert api_key == "test-anthropic-key"

    def test_get_active_api_key_openai(self) -> None:
        """Test getting API key for OpenAI provider."""
        config = ReelsbotConfig(
            llm_provider="openai",
            openai_api_key="test-openai-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )

        api_key = config.get_active_api_key()
        assert api_key == "test-openai-key"

    def test_get_active_api_key_missing(self) -> None:
        """Test error when API key is missing for active provider."""
        config = ReelsbotConfig(
            llm_provider="anthropic",
            anthropic_api_key="",
            default_a_ratio=70,
            default_e_ratio=30,
        )

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is not set"):
            config.get_active_api_key()

    def test_get_active_model(self) -> None:
        """Test getting model name for active provider."""
        config1 = ReelsbotConfig(
            llm_provider="anthropic",
            anthropic_model="claude-sonnet-4-20250514",
            anthropic_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )
        assert config1.get_active_model() == "claude-sonnet-4-20250514"

        config2 = ReelsbotConfig(
            llm_provider="openai",
            openai_model="gpt-4-turbo",
            openai_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )
        assert config2.get_active_model() == "gpt-4-turbo"

    def test_validate_config_creates_directories(self, tmp_path: Path) -> None:
        """Test that validate_config creates required directories."""
        outputs_dir = tmp_path / "outputs"
        logs_dir = tmp_path / "logs"

        config = ReelsbotConfig(
            anthropic_api_key="test-key",
            default_a_ratio=70,
            default_e_ratio=30,
            outputs_dir=outputs_dir,
            logs_dir=logs_dir,
        )

        # Directories shouldn't exist yet
        assert not outputs_dir.exists()
        assert not logs_dir.exists()

        # Validate config
        config.validate_config()

        # Directories should now exist
        assert outputs_dir.exists()
        assert logs_dir.exists()
