"""Configuration management for reelsbot using Pydantic Settings.

This module provides type-safe configuration management with environment variable loading,
validation, and sensible defaults for the Instagram Reels automation system.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReelsbotConfig(BaseSettings):
    """Type-safe configuration for reelsbot with environment variable support.

    Configuration is loaded from environment variables and .env file.
    All settings have validation and sensible defaults where appropriate.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Provider Settings
    llm_provider: Literal["anthropic", "openai"] = Field(
        default="openai",
        description="LLM provider to use (anthropic or openai)",
    )

    # OpenAI Settings (primary)
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT models",
    )
    openai_model: str = Field(
        default="gpt-5-mini",
        description="OpenAI model to use (GPT-5 mini - faster, cost-efficient)",
    )

    # Anthropic Settings (alternative)
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude models",
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model to use",
    )

    # LLM Generation Settings
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation (0.0-2.0)",
    )
    llm_max_tokens: int = Field(
        default=2000,
        ge=100,
        le=8000,
        description="Maximum tokens for LLM generation",
    )

    # Video Duration Settings (in seconds)
    default_a_duration_min: int = Field(
        default=8,
        ge=5,
        le=60,
        description="Minimum duration for abstract (A) videos in seconds",
    )
    default_a_duration_max: int = Field(
        default=12,
        ge=5,
        le=60,
        description="Maximum duration for abstract (A) videos in seconds",
    )
    default_e_duration_min: int = Field(
        default=10,
        ge=5,
        le=60,
        description="Minimum duration for educational (E) videos in seconds",
    )
    default_e_duration_max: int = Field(
        default=14,
        ge=5,
        le=60,
        description="Maximum duration for educational (E) videos in seconds",
    )

    # Video Quality Settings
    video_resolution: tuple[int, int] = Field(
        default=(1080, 1920),
        description="Video resolution as (width, height) for Instagram Reels",
    )
    video_aspect_ratio: str = Field(
        default="9:16",
        description="Video aspect ratio for Instagram Reels",
    )
    video_fps: int = Field(
        default=30,
        ge=24,
        le=60,
        description="Video frames per second",
    )

    # Safety Settings
    policy_max_retry: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for policy violations",
    )
    blocked_terms_path: Path = Field(
        default=Path("policies/blocked_terms.txt"),
        description="Path to blocked terms file",
    )

    # A/E Mix Ratio (percentages)
    default_a_ratio: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Percentage of abstract (A) content in mix",
    )
    default_e_ratio: int = Field(
        default=30,
        ge=0,
        le=100,
        description="Percentage of educational (E) content in mix",
    )

    # Path Settings
    outputs_dir: Path = Field(
        default=Path("outputs"),
        description="Directory for output files",
    )
    logs_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files",
    )

    # FFmpeg Settings
    ffmpeg_path: str = Field(
        default="ffmpeg",
        description="Path to ffmpeg executable (or command if in PATH)",
    )

    # Future: Meta Graph API Settings (not used in MVP)
    meta_access_token: str = Field(
        default="",
        description="Meta Graph API access token (future use)",
    )
    instagram_account_id: str = Field(
        default="",
        description="Instagram account ID (future use)",
    )

    @field_validator("default_a_duration_min", "default_a_duration_max")
    @classmethod
    def validate_a_duration(cls, v: int, info) -> int:
        """Validate abstract video duration range."""
        if info.field_name == "default_a_duration_max":
            # We can't access other fields during validation, so just ensure max >= min
            # The model_validator below will handle cross-field validation
            pass
        return v

    @field_validator("default_e_duration_min", "default_e_duration_max")
    @classmethod
    def validate_e_duration(cls, v: int, info) -> int:
        """Validate educational video duration range."""
        if info.field_name == "default_e_duration_max":
            # Cross-field validation handled in model_validator
            pass
        return v

    def validate_config(self) -> None:
        """Validate configuration after loading.

        Raises:
            ValueError: If configuration is invalid.
        """
        # Validate API key presence for selected provider
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'. "
                "Please set it in your .env file."
            )
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'. "
                "Please set it in your .env file."
            )

        # Validate duration ranges
        if self.default_a_duration_min > self.default_a_duration_max:
            raise ValueError(
                f"DEFAULT_A_DURATION_MIN ({self.default_a_duration_min}) "
                f"cannot be greater than DEFAULT_A_DURATION_MAX ({self.default_a_duration_max})"
            )
        if self.default_e_duration_min > self.default_e_duration_max:
            raise ValueError(
                f"DEFAULT_E_DURATION_MIN ({self.default_e_duration_min}) "
                f"cannot be greater than DEFAULT_E_DURATION_MAX ({self.default_e_duration_max})"
            )

        # Validate A/E ratio sums to 100
        if self.default_a_ratio + self.default_e_ratio != 100:
            raise ValueError(
                f"A/E ratio must sum to 100. "
                f"Got A={self.default_a_ratio}, E={self.default_e_ratio}"
            )

        # Validate paths exist (create directories if needed)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def get_active_api_key(self) -> str:
        """Get the API key for the active LLM provider.

        Returns:
            API key string for the active provider.

        Raises:
            ValueError: If API key is not set for active provider.
        """
        if self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is not set")
            return self.anthropic_api_key
        elif self.llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set")
            return self.openai_api_key
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def get_active_model(self) -> str:
        """Get the model name for the active LLM provider.

        Returns:
            Model name string for the active provider.
        """
        if self.llm_provider == "anthropic":
            return self.anthropic_model
        elif self.llm_provider == "openai":
            return self.openai_model
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")


def load_config() -> ReelsbotConfig:
    """Load and validate configuration from environment.

    Returns:
        Validated ReelsbotConfig instance.

    Raises:
        ValidationError: If configuration validation fails.
        ValueError: If configuration is invalid.
    """
    try:
        config = ReelsbotConfig()
        config.validate_config()
        return config
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}") from e
