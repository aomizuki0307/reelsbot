"""Fictional brand name generation for reelsbot content.

This module provides utilities for generating safe, fictional brand names
that avoid real brand similarities and follow specified constraints.
"""

import random
from typing import List


class BrandNameGenerator:
    """Generator for fictional brand names following specific constraints.

    Brand names are composed of a common noun prefix and a coined suffix.
    The generator ensures names are:
    - 7-14 characters total
    - English letters only (no numbers/symbols)
    - Free from real brand name fragments
    - Unique and memorable

    Examples:
        >>> generator = BrandNameGenerator()
        >>> brand = generator.generate()
        >>> print(brand)
        'WaveVoria'
    """

    # Common nouns for brand prefixes
    COMMON_NOUNS: List[str] = [
        "Wave",
        "Peak",
        "Echo",
        "Flux",
        "Aura",
        "Pulse",
        "Drift",
        "Spark",
        "Glow",
        "Haze",
        "Mist",
        "Bloom",
    ]

    # Syllables for coined suffixes (2-3 syllables per name)
    SYLLABLES: List[str] = [
        "vo",
        "ri",
        "ka",
        "ne",
        "lu",
        "ma",
        "ti",
        "so",
        "ra",
        "vi",
        "ta",
        "nu",
        "ko",
        "fe",
        "la",
    ]

    # Forbidden fragments that resemble real brands
    FORBIDDEN_FRAGMENTS: List[str] = [
        "apple",
        "nike",
        "meta",
        "amazon",
        "google",
        "face",
        "micro",
        "insta",
        "you",
        "tube",
        "samsung",
        "sony",
        "canon",
        "adidas",
        "pepsi",
        "coca",
        "cola",
    ]

    def __init__(self, seed: int | None = None) -> None:
        """Initialize brand name generator.

        Args:
            seed: Optional random seed for reproducible generation.
        """
        self.random = random.Random(seed)

    def generate(self) -> str:
        """Generate a fictional brand name.

        Returns:
            A brand name string (7-14 characters, letters only).

        The name format is: CommonNoun + 2-3 syllables
        Generation continues until a valid name is produced.

        Examples:
            >>> generator = BrandNameGenerator(seed=42)
            >>> generator.generate()
            'PeakMalune'
        """
        max_attempts = 100
        for _ in range(max_attempts):
            # Choose a random common noun
            noun = self.random.choice(self.COMMON_NOUNS)

            # Generate 2-3 syllable suffix
            num_syllables = self.random.randint(2, 3)
            syllables = [self.random.choice(self.SYLLABLES) for _ in range(num_syllables)]
            suffix = "".join(syllables)

            # Capitalize first letter of suffix
            suffix = suffix.capitalize()

            # Combine to form brand name
            brand_name = noun + suffix

            # Validate the generated name
            if self.is_safe(brand_name) and 7 <= len(brand_name) <= 14:
                return brand_name

        # Fallback: If we can't generate a valid name, use a simple combination
        # This should rarely happen with current constraints
        return self.COMMON_NOUNS[0] + "Voria"

    def is_safe(self, brand: str) -> bool:
        """Check if a brand name is safe to use.

        A brand name is safe if it:
        - Contains only English letters
        - Does not contain forbidden brand fragments
        - Is within length constraints (7-14 characters)

        Args:
            brand: Brand name string to validate.

        Returns:
            True if the brand name is safe, False otherwise.

        Examples:
            >>> generator = BrandNameGenerator()
            >>> generator.is_safe("WaveVoria")
            True
            >>> generator.is_safe("AppleCore")
            False
            >>> generator.is_safe("Wave123")
            False
        """
        # Check length
        if not (7 <= len(brand) <= 14):
            return False

        # Check for letters only
        if not brand.isalpha():
            return False

        # Check for forbidden fragments (case-insensitive)
        brand_lower = brand.lower()
        for fragment in self.FORBIDDEN_FRAGMENTS:
            if fragment in brand_lower:
                return False

        return True

    def generate_batch(self, count: int = 10) -> List[str]:
        """Generate multiple unique brand names.

        Args:
            count: Number of brand names to generate.

        Returns:
            List of unique brand name strings.

        Examples:
            >>> generator = BrandNameGenerator(seed=42)
            >>> brands = generator.generate_batch(5)
            >>> len(brands)
            5
            >>> len(set(brands)) == len(brands)  # All unique
            True
        """
        brands: set[str] = set()
        max_attempts = count * 10

        attempts = 0
        while len(brands) < count and attempts < max_attempts:
            brand = self.generate()
            brands.add(brand)
            attempts += 1

        return list(brands)


def generate_brand_name(seed: int | None = None) -> str:
    """Convenience function to generate a single brand name.

    Args:
        seed: Optional random seed for reproducible generation.

    Returns:
        A fictional brand name string.

    Examples:
        >>> brand = generate_brand_name()
        >>> 7 <= len(brand) <= 14
        True
    """
    generator = BrandNameGenerator(seed=seed)
    return generator.generate()
