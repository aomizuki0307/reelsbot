"""Caption generator for Instagram Reels.

This module generates captions and hashtags for both abstract (A) and
educational/fictional (E) type content using templates and LLM.
"""

import logging
import re
from pathlib import Path

from reelsbot.config import ReelsbotConfig
from reelsbot.llm_client import LLMClient
from reelsbot.models import ReelPlan


class CaptionGeneratorError(Exception):
    """Exception raised for errors during caption generation."""

    pass


class CaptionGenerator:
    """Caption and hashtag generator for Instagram Reels.

    Generates engaging captions using templates and LLM-based dynamic content.
    Handles both abstract (A) and educational/fictional (E) content types.

    Attributes:
        config: Reelsbot configuration instance.
        llm_client: LLM client for text generation.
        logger: Logger instance for tracking operations.
        template_a: Template for A-type captions.
        template_e: Template for E-type captions.
        hashtags_a: Safe hashtags for A-type content.
        hashtags_e: Safe hashtags for E-type content.
    """

    def __init__(
        self,
        config: ReelsbotConfig,
        llm_client: LLMClient,
        logger: logging.Logger,
    ) -> None:
        """Initialize the caption generator.

        Args:
            config: Reelsbot configuration.
            llm_client: Initialized LLM client.
            logger: Logger instance.

        Raises:
            FileNotFoundError: If caption template file is not found.
        """
        self.config = config
        self.llm_client = llm_client
        self.logger = logger

        # Load caption templates
        template_path = Path("prompts/caption_en.txt")
        if not template_path.exists():
            raise FileNotFoundError(
                f"Caption template not found at: {template_path}"
            )

        self._load_templates(template_path)
        self.logger.info("Caption generator initialized with templates loaded")

    async def generate_caption(self, plan: ReelPlan) -> tuple[str, list[str]]:
        """Generate caption and hashtags for a content plan.

        Creates a caption based on the plan type (A or E) using templates
        and plan details. Also selects appropriate hashtags.

        Args:
            plan: Content plan to generate caption for.

        Returns:
            Tuple of (caption, hashtags):
                - caption: Generated caption text (without hashtags).
                - hashtags: List of 8-12 safe hashtags (without # prefix).

        Raises:
            CaptionGeneratorError: If caption generation fails.

        Examples:
            >>> caption, hashtags = await generator.generate_caption(plan)
            >>> print(f"{caption}\\n\\n{' '.join(f'#{tag}' for tag in hashtags)}")
        """
        self.logger.debug(
            f"Generating caption for {plan.type}-type: {plan.get_display_title()}"
        )

        try:
            if plan.type == "A":
                caption = self._generate_a_caption(plan)
                hashtags = self._select_hashtags(self.hashtags_a, count=10)
            elif plan.type == "E":
                caption = self._generate_e_caption(plan)
                hashtags = self._select_hashtags(self.hashtags_e, count=10)
            else:
                raise CaptionGeneratorError(f"Unknown plan type: {plan.type}")

            self.logger.info(
                f"Caption generated: {len(caption)} chars, {len(hashtags)} hashtags"
            )
            return caption, hashtags

        except Exception as e:
            raise CaptionGeneratorError(
                f"Failed to generate caption: {e}"
            ) from e

    def _load_templates(self, template_path: Path) -> None:
        """Load caption templates from file.

        Parses the template file to extract A and E type templates
        and suggested hashtags.

        Args:
            template_path: Path to caption template file.

        Raises:
            CaptionGeneratorError: If template parsing fails.
        """
        content = template_path.read_text(encoding="utf-8")

        # Parse [A] section
        a_match = re.search(
            r"\[A\]\s*\n(.*?)(?:\[E\]|$)",
            content,
            re.DOTALL,
        )
        if not a_match:
            raise CaptionGeneratorError("Could not find [A] section in template")

        a_section = a_match.group(1)

        # Extract A template (first non-comment, non-hashtag line)
        a_lines = []
        for line in a_section.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("{"):
                a_lines.append(line)

        # Template is lines with placeholders
        template_lines = []
        for line in a_section.split("\n"):
            line = line.strip()
            if "{" in line and not line.startswith("#"):
                template_lines.append(line)

        self.template_a = "\n".join(template_lines) if template_lines else a_lines[0] if a_lines else ""

        # Extract A hashtags
        a_hashtags_match = re.search(
            r"#\w+(?:\s+#\w+)*",
            a_section,
        )
        if a_hashtags_match:
            self.hashtags_a = [
                tag.strip("#") for tag in a_hashtags_match.group(0).split()
            ]
        else:
            self.hashtags_a = [
                "oddlysatisfying",
                "abstractart",
                "loop",
                "motiondesign",
                "generativeart",
                "digitalart",
                "animation",
                "visuals",
                "calm",
                "aesthetic",
            ]

        # Parse [E] section
        e_match = re.search(
            r"\[E\]\s*\n(.*?)$",
            content,
            re.DOTALL,
        )
        if not e_match:
            raise CaptionGeneratorError("Could not find [E] section in template")

        e_section = e_match.group(1)

        # Extract E template
        template_lines = []
        for line in e_section.split("\n"):
            line = line.strip()
            if "{" in line and not line.startswith("#"):
                template_lines.append(line)

        self.template_e = "\n".join(template_lines) if template_lines else ""

        # Extract E hashtags
        e_hashtags_match = re.search(
            r"#\w+(?:\s+#\w+)*",
            e_section,
        )
        if e_hashtags_match:
            self.hashtags_e = [
                tag.strip("#") for tag in e_hashtags_match.group(0).split()
            ]
        else:
            self.hashtags_e = [
                "conceptdesign",
                "fictional",
                "productdesign",
                "graphicdesign",
                "packagingdesign",
                "3drender",
                "designconcept",
                "visualidentity",
                "branding",
                "designinspiration",
            ]

        self.logger.debug(
            f"Templates loaded: A ({len(self.template_a)} chars), "
            f"E ({len(self.template_e)} chars)"
        )

    def _generate_a_caption(self, plan: ReelPlan) -> str:
        """Generate caption for abstract (A) type content.

        Args:
            plan: A-type content plan.

        Returns:
            Generated caption text.
        """
        # Use template with placeholders
        if not self.template_a:
            # Fallback
            return f"{plan.tagline}\nA {plan.mood} loop for a quick reset.\nSave if you want more."

        caption = self.template_a

        # Replace placeholders
        replacements = {
            "{tagline}": plan.tagline or "Visual loop",
            "{mood}": plan.mood or "calm",
            "{theme}": plan.theme or "abstract",
        }

        for placeholder, value in replacements.items():
            caption = caption.replace(placeholder, value)

        return caption.strip()

    def _generate_e_caption(self, plan: ReelPlan) -> str:
        """Generate caption for educational/fictional (E) type content.

        Args:
            plan: E-type content plan.

        Returns:
            Generated caption text.
        """
        # Use template with placeholders
        if not self.template_e:
            # Fallback
            return f"Fictional concept design: {plan.concept_title}\nInvented brand: {plan.brand_name}\nThoughts?"

        caption = self.template_e

        # Replace placeholders
        replacements = {
            "{brand}": plan.brand_name or "Unknown Brand",
            "{concept}": plan.concept_title or "Concept Design",
            "{category}": plan.category or "design",
        }

        for placeholder, value in replacements.items():
            caption = caption.replace(placeholder, value)

        return caption.strip()

    def _select_hashtags(self, hashtag_pool: list[str], count: int = 10) -> list[str]:
        """Select hashtags from pool.

        Args:
            hashtag_pool: Available hashtags.
            count: Number of hashtags to select (8-12).

        Returns:
            List of selected hashtags.
        """
        # Ensure count is in valid range
        count = max(8, min(12, count))

        # Select up to count hashtags from pool
        # For now, just return the first N
        # In production, you might randomize or use LLM to select most relevant
        selected = hashtag_pool[:count]

        # Pad if needed
        while len(selected) < 8:
            selected.append("viral")

        return selected[:count]

    def get_available_hashtags(self, plan_type: str) -> list[str]:
        """Get available hashtags for a plan type.

        Args:
            plan_type: "A" or "E".

        Returns:
            List of available hashtags.
        """
        if plan_type == "A":
            return self.hashtags_a.copy()
        elif plan_type == "E":
            return self.hashtags_e.copy()
        else:
            return []
