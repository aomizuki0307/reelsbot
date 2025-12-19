"""LLM client abstraction for unified Anthropic and OpenAI API access.

This module provides a unified interface for interacting with both Anthropic (Claude)
and OpenAI (GPT) models, with automatic retry logic and error handling.
"""

import logging
from typing import Literal

from anthropic import Anthropic, APIError as AnthropicAPIError
from openai import OpenAI, APIError as OpenAIAPIError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from reelsbot.config import ReelsbotConfig


class LLMError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMClient:
    """Unified client for LLM API access with retry logic.

    Supports both Anthropic (Claude) and OpenAI (GPT) models through a single interface.
    Automatically handles retries for transient API errors with exponential backoff.

    Attributes:
        config: Reelsbot configuration instance.
        provider: Active LLM provider ("anthropic" or "openai").
        logger: Logger instance for tracking operations.
    """

    def __init__(self, config: ReelsbotConfig, logger: logging.Logger | None = None) -> None:
        """Initialize LLM client with configuration.

        Args:
            config: Reelsbot configuration with LLM settings.
            logger: Optional logger instance (creates new one if not provided).

        Raises:
            ValueError: If provider is unsupported or API key is missing.
        """
        self.config = config
        self.provider = config.llm_provider
        self.logger = logger or logging.getLogger("reelsbot")

        # Initialize the appropriate client
        if self.provider == "anthropic":
            self._anthropic_client = Anthropic(api_key=config.get_active_api_key())
            self._openai_client = None
        elif self.provider == "openai":
            self._openai_client = OpenAI(api_key=config.get_active_api_key())
            self._anthropic_client = None
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        self.logger.info(f"LLM client initialized with provider: {self.provider}")

    @retry(
        retry=retry_if_exception_type((AnthropicAPIError, OpenAIAPIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text using the configured LLM.

        Automatically retries up to 3 times with exponential backoff on API errors.

        Args:
            system_prompt: System/instruction prompt for the LLM.
            user_prompt: User message/query for the LLM.
            temperature: Sampling temperature (uses config default if None).
            max_tokens: Maximum tokens to generate (uses config default if None).

        Returns:
            Generated text string from the LLM.

        Raises:
            LLMError: If generation fails after all retries.

        Examples:
            >>> client = LLMClient(config)
            >>> response = await client.generate(
            ...     system_prompt="You are a helpful assistant.",
            ...     user_prompt="Write a short poem about coding."
            ... )
        """
        # Use config defaults if not specified
        if temperature is None:
            temperature = self.config.llm_temperature
        if max_tokens is None:
            max_tokens = self.config.llm_max_tokens

        self.logger.debug(
            f"Generating with {self.provider} "
            f"(temp={temperature}, max_tokens={max_tokens})"
        )

        try:
            if self.provider == "anthropic":
                return await self._generate_anthropic(
                    system_prompt, user_prompt, temperature, max_tokens
                )
            elif self.provider == "openai":
                return await self._generate_openai(
                    system_prompt, user_prompt, temperature, max_tokens
                )
            else:
                raise LLMError(f"Unsupported provider: {self.provider}")

        except (AnthropicAPIError, OpenAIAPIError) as e:
            self.logger.error(f"LLM API error after retries: {e}")
            raise LLMError(f"LLM generation failed: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during LLM generation: {e}")
            raise LLMError(f"LLM generation failed: {e}") from e

    async def _generate_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate text using Anthropic's Claude API.

        Args:
            system_prompt: System instruction for Claude.
            user_prompt: User message for Claude.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text from Claude.
        """
        if self._anthropic_client is None:
            raise LLMError("Anthropic client not initialized")

        response = self._anthropic_client.messages.create(
            model=self.config.get_active_model(),
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract text from response
        if response.content and len(response.content) > 0:
            content_block = response.content[0]
            if hasattr(content_block, "text"):
                return content_block.text

        raise LLMError("Empty response from Anthropic API")

    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate text using OpenAI's GPT API.

        Args:
            system_prompt: System instruction for GPT.
            user_prompt: User message for GPT.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text from GPT.
        """
        if self._openai_client is None:
            raise LLMError("OpenAI client not initialized")

        response = self._openai_client.chat.completions.create(
            model=self.config.get_active_model(),
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        # Extract text from response
        if response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            if message.content:
                return message.content

        raise LLMError("Empty response from OpenAI API")

    def get_model_info(self) -> dict[str, str]:
        """Get information about the active model.

        Returns:
            Dictionary with provider and model information.
        """
        return {
            "provider": self.provider,
            "model": self.config.get_active_model(),
        }


async def create_llm_client(
    config: ReelsbotConfig, logger: logging.Logger | None = None
) -> LLMClient:
    """Factory function to create an LLM client.

    Args:
        config: Reelsbot configuration.
        logger: Optional logger instance.

    Returns:
        Initialized LLM client.

    Examples:
        >>> config = load_config()
        >>> client = await create_llm_client(config)
    """
    return LLMClient(config, logger)
