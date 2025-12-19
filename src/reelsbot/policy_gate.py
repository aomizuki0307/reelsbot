"""Policy gate for content safety validation.

This module implements dual-layer validation:
1. Rule-based: Checks text against blocked terms list
2. LLM-based: Evaluates fictional brand names for similarity to real brands
"""

import logging
import re
from pathlib import Path

from reelsbot.config import ReelsbotConfig
from reelsbot.llm_client import LLMClient
from reelsbot.models import ReelPlan


class PolicyViolationError(Exception):
    """Exception raised when a plan violates content policy.

    Raised after maximum retry attempts are exhausted and the plan
    cannot be validated.
    """

    pass


class PolicyGate:
    """Content safety validation with dual-layer checking.

    Validates content plans against both rule-based blocked terms and
    LLM-based brand safety checks to ensure content is safe for publication.

    Attributes:
        config: Reelsbot configuration instance.
        llm_client: LLM client for brand safety checks.
        logger: Logger instance for tracking operations.
        blocked_terms: Set of blocked terms (case-insensitive).
        policy_prompt: Loaded policy system prompt for LLM.
    """

    def __init__(
        self,
        config: ReelsbotConfig,
        llm_client: LLMClient,
        logger: logging.Logger,
    ) -> None:
        """Initialize the policy gate.

        Args:
            config: Reelsbot configuration.
            llm_client: Initialized LLM client.
            logger: Logger instance.

        Raises:
            FileNotFoundError: If blocked terms or policy prompt files are not found.
        """
        self.config = config
        self.llm_client = llm_client
        self.logger = logger

        # Load blocked terms
        self.blocked_terms = self._load_blocked_terms()
        self.logger.info(f"Loaded {len(self.blocked_terms)} blocked terms")

        # Load policy system prompt
        prompt_path = Path("prompts/policy_system.txt")
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Policy system prompt not found at: {prompt_path}"
            )

        self.policy_prompt = prompt_path.read_text(encoding="utf-8")
        self.logger.info("Policy gate initialized with prompts loaded")

    async def validate_plan(self, plan: ReelPlan) -> tuple[bool, str]:
        """Validate a content plan against safety policies.

        Performs two-stage validation:
        1. Rule-based check against blocked terms
        2. LLM brand safety check (E-type only)

        Args:
            plan: Content plan to validate.

        Returns:
            Tuple of (is_valid, reason):
                - is_valid: True if plan passes all checks, False otherwise.
                - reason: Human-readable reason for validation result.

        Examples:
            >>> is_valid, reason = await gate.validate_plan(plan)
            >>> if not is_valid:
            ...     print(f"Plan rejected: {reason}")
        """
        # Stage 1: Rule-based validation
        self.logger.debug(f"Validating plan: {plan.type}-type, {plan.theme}")

        rule_valid, rule_reason = self._rule_based_check(plan)
        if not rule_valid:
            self.logger.warning(f"Rule-based check failed: {rule_reason}")
            return False, rule_reason

        # Stage 2: LLM brand safety check (E-type only)
        if plan.type == "E" and plan.brand_name:
            llm_valid, llm_reason = await self._llm_brand_safety_check(
                plan.brand_name
            )
            if not llm_valid:
                self.logger.warning(f"LLM brand safety check failed: {llm_reason}")
                return False, llm_reason

        self.logger.info(f"Plan validated successfully: {plan.get_display_title()}")
        return True, "Plan passes all safety checks"

    def _load_blocked_terms(self) -> set[str]:
        """Load blocked terms from configuration file.

        Returns:
            Set of blocked terms (lowercase, stripped).

        Raises:
            FileNotFoundError: If blocked terms file is not found.
        """
        terms_path = self.config.blocked_terms_path

        if not terms_path.exists():
            raise FileNotFoundError(
                f"Blocked terms file not found at: {terms_path}"
            )

        terms = set()
        with terms_path.open("r", encoding="utf-8") as f:
            for line in f:
                # Strip whitespace and lowercase
                line = line.strip().lower()

                # Ignore empty lines and comments
                if not line or line.startswith("#"):
                    continue

                terms.add(line)

        return terms

    def _rule_based_check(self, plan: ReelPlan) -> tuple[bool, str]:
        """Check plan text fields against blocked terms.

        Uses word boundary matching for accurate detection.

        Args:
            plan: Plan to check.

        Returns:
            Tuple of (is_valid, reason).
        """
        # Collect all text fields to check
        text_fields = []

        if plan.theme:
            text_fields.append(("theme", plan.theme))
        if plan.mood:
            text_fields.append(("mood", plan.mood))
        if plan.tagline:
            text_fields.append(("tagline", plan.tagline))
        if plan.brand_name:
            text_fields.append(("brand_name", plan.brand_name))
        if plan.concept_title:
            text_fields.append(("concept_title", plan.concept_title))
        if plan.category:
            text_fields.append(("category", plan.category))

        # Check each field
        for field_name, field_value in text_fields:
            if not field_value:
                continue

            field_lower = field_value.lower()

            # Check against blocked terms using word boundaries
            for term in self.blocked_terms:
                # Create word boundary pattern
                # Use \b for word boundaries, but handle multi-word terms
                if " " in term:
                    # Multi-word term: match exact phrase
                    pattern = r"\b" + re.escape(term) + r"\b"
                else:
                    # Single word: match with word boundaries
                    pattern = r"\b" + re.escape(term) + r"\b"

                if re.search(pattern, field_lower):
                    reason = (
                        f"Blocked term '{term}' found in {field_name}: "
                        f"'{field_value}'"
                    )
                    return False, reason

        return True, "No blocked terms found"

    async def _llm_brand_safety_check(self, brand_name: str) -> tuple[bool, str]:
        """Use LLM to check if brand name is too similar to real brands.

        Args:
            brand_name: Fictional brand name to check.

        Returns:
            Tuple of (is_safe, reason).
        """
        self.logger.debug(f"LLM brand safety check for: {brand_name}")

        user_prompt = f"""Evaluate this fictional brand name: "{brand_name}"

Is this name safe to use, or is it too similar to an existing real brand?"""

        try:
            # Use temperature=0.0 for deterministic results
            response = await self.llm_client.generate(
                system_prompt=self.policy_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
            )
        except Exception as e:
            # On LLM error, fail safe (reject the plan)
            reason = f"LLM safety check failed (error): {e}"
            self.logger.error(reason)
            return False, reason

        # Parse response
        response_upper = response.upper()

        if "**SAFE**" in response_upper or response_upper.strip().startswith("SAFE"):
            # Extract reason if available
            reason_match = re.search(
                r"\*\*SAFE\*\*\s*-\s*(.+)",
                response,
                re.IGNORECASE | re.DOTALL,
            )
            if reason_match:
                reason = reason_match.group(1).strip()
            else:
                reason = "Brand name is safe (no resemblance to real brands)"

            self.logger.debug(f"Brand '{brand_name}' marked SAFE: {reason}")
            return True, reason

        elif "**UNSAFE**" in response_upper or response_upper.strip().startswith(
            "UNSAFE"
        ):
            # Extract reason if available
            reason_match = re.search(
                r"\*\*UNSAFE\*\*\s*-\s*(.+)",
                response,
                re.IGNORECASE | re.DOTALL,
            )
            if reason_match:
                reason = reason_match.group(1).strip()
            else:
                reason = "Brand name too similar to real brand"

            self.logger.warning(f"Brand '{brand_name}' marked UNSAFE: {reason}")
            return False, f"Brand safety issue: {reason}"

        else:
            # Ambiguous response - fail safe
            reason = f"Ambiguous LLM response: {response[:100]}"
            self.logger.warning(f"Ambiguous brand safety response for '{brand_name}'")
            return False, reason

    def get_blocked_terms_count(self) -> int:
        """Get the number of loaded blocked terms.

        Returns:
            Count of blocked terms.
        """
        return len(self.blocked_terms)

    def is_term_blocked(self, term: str) -> bool:
        """Check if a specific term is in the blocked list.

        Args:
            term: Term to check (case-insensitive).

        Returns:
            True if term is blocked, False otherwise.
        """
        return term.lower() in self.blocked_terms
