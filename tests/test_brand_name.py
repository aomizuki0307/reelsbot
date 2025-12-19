"""Tests for brand name generator."""

import pytest

from reelsbot.utils.brand_name import BrandNameGenerator, generate_brand_name


class TestBrandNameGenerator:
    """Tests for BrandNameGenerator class."""

    def test_generate_returns_valid_brand(self) -> None:
        """Test that generated brand names are valid."""
        generator = BrandNameGenerator(seed=42)
        brand = generator.generate()

        # Check basic properties
        assert isinstance(brand, str)
        assert 7 <= len(brand) <= 14
        assert brand.isalpha()

    def test_generate_reproducible_with_seed(self) -> None:
        """Test that same seed produces same brand names."""
        gen1 = BrandNameGenerator(seed=123)
        gen2 = BrandNameGenerator(seed=123)

        brand1 = gen1.generate()
        brand2 = gen2.generate()

        assert brand1 == brand2

    def test_generate_different_without_seed(self) -> None:
        """Test that different instances produce different names."""
        gen1 = BrandNameGenerator()
        gen2 = BrandNameGenerator()

        # Generate multiple brands from each
        brands1 = gen1.generate_batch(10)
        brands2 = gen2.generate_batch(10)

        # At least some should be different (very unlikely to be all the same)
        assert brands1 != brands2

    def test_is_safe_valid_brands(self) -> None:
        """Test that valid brand names pass safety check."""
        generator = BrandNameGenerator()

        assert generator.is_safe("WaveVoria")
        assert generator.is_safe("PeakMalune")
        assert generator.is_safe("EchoTivra")

    def test_is_safe_rejects_forbidden_fragments(self) -> None:
        """Test that brands with forbidden fragments are rejected."""
        generator = BrandNameGenerator()

        # Test each forbidden fragment
        forbidden_brands = [
            "AppleCore",
            "NikeWave",
            "MetaPeak",
            "AmazonEcho",
            "GoogleFlow",
            "FaceTime",
            "MicroSoft",
            "InstaGram",
            "YouTube",
        ]

        for brand in forbidden_brands:
            assert not generator.is_safe(brand), f"Should reject brand: {brand}"

    def test_is_safe_rejects_non_alpha(self) -> None:
        """Test that brands with non-alphabetic characters are rejected."""
        generator = BrandNameGenerator()

        assert not generator.is_safe("Wave123")
        assert not generator.is_safe("Peak-Flow")
        assert not generator.is_safe("Echo_Voria")
        assert not generator.is_safe("Flux@Peak")

    def test_is_safe_rejects_wrong_length(self) -> None:
        """Test that brands outside length range are rejected."""
        generator = BrandNameGenerator()

        # Too short
        assert not generator.is_safe("Wave")
        assert not generator.is_safe("Hi")

        # Too long
        assert not generator.is_safe("WaveVoriaExtraLong")
        assert not generator.is_safe("A" * 20)

    def test_generate_batch_returns_correct_count(self) -> None:
        """Test that generate_batch returns requested number of brands."""
        generator = BrandNameGenerator(seed=42)

        brands = generator.generate_batch(5)
        assert len(brands) == 5

        brands = generator.generate_batch(10)
        assert len(brands) == 10

    def test_generate_batch_returns_unique_brands(self) -> None:
        """Test that generate_batch returns unique brand names."""
        generator = BrandNameGenerator(seed=42)

        brands = generator.generate_batch(20)

        # All brands should be unique
        assert len(brands) == len(set(brands))

    def test_generate_brand_name_convenience_function(self) -> None:
        """Test the convenience function for generating brand names."""
        brand = generate_brand_name(seed=42)

        assert isinstance(brand, str)
        assert 7 <= len(brand) <= 14
        assert brand.isalpha()

    def test_brand_format(self) -> None:
        """Test that generated brands follow the expected format."""
        generator = BrandNameGenerator(seed=42)

        # Generate several brands and check they follow the pattern
        for _ in range(10):
            brand = generator.generate()

            # Should start with a capitalized noun
            assert brand[0].isupper()

            # Should be all letters
            assert brand.isalpha()

            # Should be within length constraints
            assert 7 <= len(brand) <= 14

    def test_brand_diversity(self) -> None:
        """Test that generator produces diverse brand names."""
        generator = BrandNameGenerator(seed=42)

        brands = generator.generate_batch(50)

        # Should have many unique brands
        assert len(set(brands)) >= 45  # Allow for some collision

        # Brands should start with different prefixes
        prefixes = {brand[:4] for brand in brands}
        assert len(prefixes) > 5  # At least several different prefixes
