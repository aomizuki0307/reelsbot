"""Content planner for Instagram Reels using LLM-based generation.

This module implements the Planner class that generates daily content plans
using an LLM to create diverse, engaging video concepts for both abstract
and educational/fictional content types.
"""

import json
import logging
import re
from pathlib import Path
from typing import Literal

from reelsbot.config import ReelsbotConfig
from reelsbot.llm_client import LLMClient
from reelsbot.models import ReelPlan


class PlannerError(Exception):
    """Exception raised for errors during content planning."""

    pass


class Planner:
    """LLM-based content planner for Instagram Reels.

    Generates creative content plans for both abstract (A) and educational/fictional (E)
    type videos using an LLM. Handles plan validation, JSON parsing, and retry logic.

    Attributes:
        config: Reelsbot configuration instance.
        llm_client: LLM client for text generation.
        logger: Logger instance for tracking operations.
        system_prompt: Loaded system prompt for the LLM.
    """

    def __init__(
        self,
        config: ReelsbotConfig,
        llm_client: LLMClient,
        logger: logging.Logger,
    ) -> None:
        """Initialize the planner.

        Args:
            config: Reelsbot configuration.
            llm_client: Initialized LLM client.
            logger: Logger instance.

        Raises:
            FileNotFoundError: If system prompt file is not found.
        """
        self.config = config
        self.llm_client = llm_client
        self.logger = logger

        # Load system prompt
        prompt_path = Path("prompts/planner_system.txt")
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Planner system prompt not found at: {prompt_path}"
            )

        self.system_prompt = prompt_path.read_text(encoding="utf-8")
        self.logger.info("Planner initialized with system prompt loaded")

    async def generate_daily_plan(
        self,
        date: str,
        count: int,
        a_ratio: int = 70,
    ) -> list[ReelPlan]:
        """Generate a daily content plan with multiple reels.

        Creates a diverse set of content plans with the specified A:E ratio.
        Plans are validated for duration ranges and required fields.

        Args:
            date: Target date for the plan (YYYY-MM-DD format).
            count: Number of reels to plan.
            a_ratio: Percentage of abstract (A) content (0-100). E ratio is 100-a_ratio.

        Returns:
            List of validated ReelPlan objects.

        Raises:
            PlannerError: If plan generation or validation fails.
            ValueError: If parameters are invalid.
        """
        if count <= 0:
            raise ValueError(f"Count must be positive, got: {count}")
        if not 0 <= a_ratio <= 100:
            raise ValueError(f"A ratio must be 0-100, got: {a_ratio}")

        e_ratio = 100 - a_ratio
        a_count = round(count * a_ratio / 100)
        e_count = count - a_count

        self.logger.info(
            f"Generating daily plan for {date}: {count} reels "
            f"(A: {a_count}, E: {e_count})"
        )

        # Create user prompt
        user_prompt = self._create_user_prompt(date, a_count, e_count)

        # Call LLM
        try:
            response = await self.llm_client.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
            )
            self.logger.debug(f"LLM response received: {len(response)} chars")
        except Exception as e:
            raise PlannerError(f"Failed to generate plan: {e}") from e

        # Parse and validate response
        try:
            plans = self._parse_llm_response(response)
        except Exception as e:
            raise PlannerError(f"Failed to parse LLM response: {e}") from e

        # Validate plan count
        if len(plans) != count:
            self.logger.warning(
                f"Expected {count} plans, got {len(plans)}. "
                f"Adjusting to match requested count."
            )
            # Take first N or pad with regenerated plans if needed
            if len(plans) > count:
                plans = plans[:count]
            elif len(plans) < count:
                # For simplicity, just use what we got
                # In production, you might regenerate missing plans
                pass

        # Validate each plan
        for i, plan in enumerate(plans):
            self._validate_plan(plan, i)

        self.logger.info(f"Successfully generated {len(plans)} validated plans")
        return plans

    async def regenerate_single_plan(
        self,
        plan_type: Literal["A", "E"],
    ) -> ReelPlan:
        """Generate a single plan of specified type.

        Used for policy retry scenarios when a plan fails validation.

        Args:
            plan_type: Type of plan to generate ("A" or "E").

        Returns:
            Single validated ReelPlan.

        Raises:
            PlannerError: If generation or validation fails.
        """
        self.logger.info(f"Regenerating single {plan_type}-type plan")

        a_count = 1 if plan_type == "A" else 0
        e_count = 1 if plan_type == "E" else 0

        user_prompt = self._create_user_prompt(
            date="retry",
            a_count=a_count,
            e_count=e_count,
        )

        try:
            response = await self.llm_client.generate(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as e:
            raise PlannerError(f"Failed to regenerate plan: {e}") from e

        try:
            plans = self._parse_llm_response(response)
        except Exception as e:
            raise PlannerError(f"Failed to parse regenerated plan: {e}") from e

        if not plans:
            raise PlannerError("No plans returned from LLM")

        plan = plans[0]
        self._validate_plan(plan, 0)

        self.logger.info(f"Successfully regenerated {plan_type}-type plan")
        return plan

    def _create_user_prompt(
        self,
        date: str,
        a_count: int,
        e_count: int,
    ) -> str:
        """Create user prompt for plan generation.

        Args:
            date: Target date string.
            a_count: Number of A-type plans to generate.
            e_count: Number of E-type plans to generate.

        Returns:
            Formatted user prompt string.
        """
        total = a_count + e_count
        prompt = f"""Generate {total} Instagram Reel content plans for {date}.

Requirements:
- {a_count} abstract (A) type videos
- {e_count} educational/fictional (E) type videos

For A-type:
- Duration: 8-12 seconds
- Include: theme, mood, tagline

For E-type:
- Duration: 10-14 seconds
- Include: category, brand_name, concept_title
- Brand names must be clearly fictional and unique

Return as a JSON array following the specified format. Ensure maximum diversity in themes and concepts."""

        return prompt

    def _parse_llm_response(self, response: str) -> list[ReelPlan]:
        """Parse LLM response into ReelPlan objects.

        Handles markdown code blocks and extracts JSON array.

        Args:
            response: Raw LLM response text.

        Returns:
            List of parsed ReelPlan objects.

        Raises:
            PlannerError: If JSON parsing fails or response is invalid.
        """
        # Extract JSON from response (handle markdown code blocks)
        json_str = self._extract_json(response)

        # Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise PlannerError(f"Invalid JSON in response: {e}") from e

        # Ensure it's a list
        if not isinstance(data, list):
            raise PlannerError(f"Expected JSON array, got: {type(data)}")

        # Parse into ReelPlan objects
        plans = []
        for i, item in enumerate(data):
            try:
                plan = ReelPlan(**item)
                plans.append(plan)
            except Exception as e:
                raise PlannerError(
                    f"Failed to parse plan {i}: {e}\nData: {item}"
                ) from e

        return plans

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks.

        Args:
            text: Text containing JSON.

        Returns:
            Extracted JSON string.

        Raises:
            PlannerError: If no JSON is found.
        """
        # Try to find JSON in markdown code blocks
        code_block_pattern = r"```(?:json)?\s*(\[.*?\])\s*```"
        match = re.search(code_block_pattern, text, re.DOTALL)

        if match:
            return match.group(1)

        # Try to find raw JSON array
        array_pattern = r"\[\s*\{.*?\}\s*\]"
        match = re.search(array_pattern, text, re.DOTALL)

        if match:
            return match.group(0)

        # If no patterns match, assume the whole text is JSON
        stripped = text.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return stripped

        raise PlannerError("Could not extract JSON from LLM response")

    def _validate_plan(self, plan: ReelPlan, index: int) -> None:
        """Validate a single plan's constraints.

        Args:
            plan: Plan to validate.
            index: Plan index for error messages.

        Raises:
            PlannerError: If validation fails.
        """
        # Validate duration ranges
        if plan.type == "A":
            min_dur = self.config.default_a_duration_min
            max_dur = self.config.default_a_duration_max
            if not min_dur <= plan.duration_sec <= max_dur:
                raise PlannerError(
                    f"Plan {index}: A-type duration {plan.duration_sec}s "
                    f"outside range [{min_dur}, {max_dur}]"
                )
        elif plan.type == "E":
            min_dur = self.config.default_e_duration_min
            max_dur = self.config.default_e_duration_max
            if not min_dur <= plan.duration_sec <= max_dur:
                raise PlannerError(
                    f"Plan {index}: E-type duration {plan.duration_sec}s "
                    f"outside range [{min_dur}, {max_dur}]"
                )

        # Type-specific field validation is handled by ReelPlan.model_post_init

        self.logger.debug(
            f"Plan {index} validated: {plan.type}-type, "
            f"{plan.duration_sec}s, {plan.theme}"
        )
