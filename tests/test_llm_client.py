"""Tests for LLM client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from reelsbot.config import ReelsbotConfig
from reelsbot.llm_client import LLMClient, LLMError, create_llm_client


class TestLLMClient:
    """Tests for LLM client abstraction."""

    @pytest.fixture
    def anthropic_config(self) -> ReelsbotConfig:
        """Create a test configuration for Anthropic."""
        return ReelsbotConfig(
            llm_provider="anthropic",
            anthropic_api_key="test-anthropic-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )

    @pytest.fixture
    def openai_config(self) -> ReelsbotConfig:
        """Create a test configuration for OpenAI."""
        return ReelsbotConfig(
            llm_provider="openai",
            openai_api_key="test-openai-key",
            default_a_ratio=70,
            default_e_ratio=30,
        )

    def test_init_anthropic(self, anthropic_config: ReelsbotConfig) -> None:
        """Test initializing client with Anthropic provider."""
        with patch("reelsbot.llm_client.Anthropic"):
            client = LLMClient(anthropic_config)

            assert client.provider == "anthropic"
            assert client.config == anthropic_config

    def test_init_openai(self, openai_config: ReelsbotConfig) -> None:
        """Test initializing client with OpenAI provider."""
        with patch("reelsbot.llm_client.OpenAI"):
            client = LLMClient(openai_config)

            assert client.provider == "openai"
            assert client.config == openai_config

    def test_get_model_info_anthropic(self, anthropic_config: ReelsbotConfig) -> None:
        """Test getting model info for Anthropic."""
        with patch("reelsbot.llm_client.Anthropic"):
            client = LLMClient(anthropic_config)
            info = client.get_model_info()

            assert info["provider"] == "anthropic"
            assert info["model"] == anthropic_config.anthropic_model

    def test_get_model_info_openai(self, openai_config: ReelsbotConfig) -> None:
        """Test getting model info for OpenAI."""
        with patch("reelsbot.llm_client.OpenAI"):
            client = LLMClient(openai_config)
            info = client.get_model_info()

            assert info["provider"] == "openai"
            assert info["model"] == openai_config.openai_model

    @pytest.mark.asyncio
    async def test_generate_anthropic(self, anthropic_config: ReelsbotConfig) -> None:
        """Test generating text with Anthropic."""
        # Mock the Anthropic client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated response from Claude")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("reelsbot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_client

            client = LLMClient(anthropic_config)
            result = await client.generate(
                system_prompt="You are helpful",
                user_prompt="Write a test response",
            )

            assert result == "Generated response from Claude"
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_openai(self, openai_config: ReelsbotConfig) -> None:
        """Test generating text with OpenAI."""
        # Mock the OpenAI client
        mock_choice = MagicMock()
        mock_choice.message.content = "Generated response from GPT"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("reelsbot.llm_client.OpenAI") as mock_openai:
            mock_openai.return_value = mock_client

            client = LLMClient(openai_config)
            result = await client.generate(
                system_prompt="You are helpful",
                user_prompt="Write a test response",
            )

            assert result == "Generated response from GPT"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_uses_config_defaults(
        self, anthropic_config: ReelsbotConfig
    ) -> None:
        """Test that generate uses config defaults for temperature and max_tokens."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("reelsbot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_client

            client = LLMClient(anthropic_config)
            await client.generate(
                system_prompt="Test system",
                user_prompt="Test user",
            )

            # Check that create was called with config defaults
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["temperature"] == anthropic_config.llm_temperature
            assert call_args.kwargs["max_tokens"] == anthropic_config.llm_max_tokens

    @pytest.mark.asyncio
    async def test_generate_respects_custom_params(
        self, anthropic_config: ReelsbotConfig
    ) -> None:
        """Test that generate respects custom temperature and max_tokens."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("reelsbot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_client

            client = LLMClient(anthropic_config)
            custom_temp = 1.5
            custom_tokens = 500

            await client.generate(
                system_prompt="Test",
                user_prompt="Test",
                temperature=custom_temp,
                max_tokens=custom_tokens,
            )

            # Check custom params were used
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["temperature"] == custom_temp
            assert call_args.kwargs["max_tokens"] == custom_tokens

    @pytest.mark.asyncio
    async def test_generate_handles_empty_response(
        self, anthropic_config: ReelsbotConfig
    ) -> None:
        """Test that generate raises error on empty response."""
        mock_response = MagicMock()
        mock_response.content = []

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with patch("reelsbot.llm_client.Anthropic") as mock_anthropic:
            mock_anthropic.return_value = mock_client

            client = LLMClient(anthropic_config)

            with pytest.raises(LLMError, match="Empty response"):
                await client.generate(
                    system_prompt="Test",
                    user_prompt="Test",
                )

    @pytest.mark.asyncio
    async def test_create_llm_client_factory(self, anthropic_config: ReelsbotConfig) -> None:
        """Test the factory function for creating LLM client."""
        with patch("reelsbot.llm_client.Anthropic"):
            client = await create_llm_client(anthropic_config)

            assert isinstance(client, LLMClient)
            assert client.provider == "anthropic"
