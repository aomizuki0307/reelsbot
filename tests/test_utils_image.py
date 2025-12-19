"""Unit tests for image utility functions."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from reelsbot.models import ReelPlan
from reelsbot.utils.image import (
    CATEGORY_COLORS,
    add_text_to_image,
    create_concept_background,
    create_thumbnail_from_image,
)


@pytest.fixture
def e_type_plan():
    """Provide a sample E-type plan."""
    return ReelPlan(
        type="E",
        theme="cafe",
        mood="calm",
        duration_sec=12,
        brand_name="ZENITHCAFE",
        concept_title="Modern Cafe Interior",
        category="cafe",
    )


@pytest.fixture
def temp_dir():
    """Provide a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestCategoryColors:
    """Test category color definitions."""

    def test_category_colors_defined(self):
        """Test that category colors are defined."""
        assert len(CATEGORY_COLORS) > 0
        assert "cafe" in CATEGORY_COLORS
        assert "packaging" in CATEGORY_COLORS
        assert "poster" in CATEGORY_COLORS
        assert "app_ui" in CATEGORY_COLORS

    def test_category_colors_are_rgb_tuples(self):
        """Test that colors are RGB tuples."""
        for category, color in CATEGORY_COLORS.items():
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)


class TestCreateConceptBackground:
    """Test background image creation for E-type videos."""

    def test_create_background_success(self, e_type_plan, temp_dir):
        """Test successful background creation."""
        bg_path = create_concept_background(e_type_plan, temp_dir)

        assert bg_path.exists()
        assert bg_path.suffix == ".png"

        # Verify image properties
        img = Image.open(bg_path)
        assert img.size == (1080, 1920)
        assert img.mode == "RGB"

    def test_create_background_wrong_type(self, temp_dir):
        """Test error when plan is not E-type."""
        plan = ReelPlan(
            type="A",
            theme="gradient",
            mood="calm",
            duration_sec=10,
            tagline="Abstract",
        )

        with pytest.raises(ValueError, match="requires E-type plan"):
            create_concept_background(plan, temp_dir)

    def test_create_background_missing_fields(self, temp_dir):
        """Test error when E-type plan missing required fields."""
        # This should fail during plan creation
        with pytest.raises(ValueError):
            plan = ReelPlan(
                type="E",
                theme="cafe",
                mood="calm",
                duration_sec=12,
                brand_name=None,  # Missing
                concept_title="Test",
                category="cafe",
            )

    def test_create_background_creates_directory(self, e_type_plan):
        """Test that temp directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "subdir"
            assert not temp_path.exists()

            bg_path = create_concept_background(e_type_plan, temp_path)

            assert temp_path.exists()
            assert bg_path.exists()

    def test_create_background_category_color(self, temp_dir):
        """Test that category-specific colors are used."""
        plan = ReelPlan(
            type="E",
            theme="packaging",
            mood="minimal",
            duration_sec=12,
            brand_name="PACKMASTER",
            concept_title="Product Packaging",
            category="packaging",
        )

        bg_path = create_concept_background(plan, temp_dir)

        img = Image.open(bg_path)
        # Check that background uses packaging color
        expected_color = CATEGORY_COLORS["packaging"]
        # Sample a pixel from the center-top (should be background)
        pixel = img.getpixel((540, 100))
        # Allow some tolerance for PIL operations
        assert all(abs(pixel[i] - expected_color[i]) <= 5 for i in range(3))

    def test_create_background_unknown_category(self, temp_dir):
        """Test fallback color for unknown category."""
        plan = ReelPlan(
            type="E",
            theme="unknown",
            mood="calm",
            duration_sec=12,
            brand_name="TESTBRAND",
            concept_title="Unknown Category",
            category="unknown_category",
        )

        # Should not raise, should use default color
        bg_path = create_concept_background(plan, temp_dir)
        assert bg_path.exists()


class TestAddTextToImage:
    """Test text addition to images."""

    def test_add_text_simple(self):
        """Test adding simple text to image."""
        img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))

        result = add_text_to_image(
            img=img,
            text="Hello World",
            position=(100, 100),
            font_size=48,
            color=(0, 0, 0),
        )

        assert result == img  # Modified in-place
        assert result.size == (1080, 1920)

    def test_add_text_center_aligned(self):
        """Test center-aligned text."""
        img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))

        result = add_text_to_image(
            img=img,
            text="Centered",
            position=(540, 960),
            font_size=48,
            color=(0, 0, 0),
            align="center",
        )

        assert result.size == (1080, 1920)

    def test_add_text_right_aligned(self):
        """Test right-aligned text."""
        img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))

        result = add_text_to_image(
            img=img,
            text="Right",
            position=(1000, 100),
            font_size=48,
            color=(0, 0, 0),
            align="right",
        )

        assert result.size == (1080, 1920)

    def test_add_text_bold(self):
        """Test adding bold text."""
        img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))

        result = add_text_to_image(
            img=img,
            text="Bold Text",
            position=(100, 100),
            font_size=48,
            color=(0, 0, 0),
            bold=True,
        )

        assert result.size == (1080, 1920)

    def test_add_text_different_colors(self):
        """Test text with different colors."""
        img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))

        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (128, 128, 128),  # Gray
        ]

        for i, color in enumerate(colors):
            add_text_to_image(
                img=img,
                text=f"Color {i}",
                position=(100, 100 + i * 100),
                font_size=36,
                color=color,
            )

        assert img.size == (1080, 1920)

    def test_add_text_various_sizes(self):
        """Test text with various font sizes."""
        img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))

        sizes = [24, 36, 48, 72, 96]

        for i, size in enumerate(sizes):
            add_text_to_image(
                img=img,
                text=f"Size {size}",
                position=(100, 100 + i * 150),
                font_size=size,
                color=(0, 0, 0),
            )

        assert img.size == (1080, 1920)


class TestCreateThumbnailFromImage:
    """Test thumbnail creation from PIL images."""

    def test_create_thumbnail_success(self, temp_dir):
        """Test successful thumbnail creation."""
        # Create source image
        img = Image.new("RGB", (1080, 1920), color=(100, 150, 200))
        thumbnail_path = temp_dir / "thumb.jpg"

        result = create_thumbnail_from_image(img, thumbnail_path)

        assert result == thumbnail_path
        assert thumbnail_path.exists()

        # Verify thumbnail
        thumb = Image.open(thumbnail_path)
        assert thumb.size[0] <= 640
        assert thumb.size[1] <= 1138

    def test_create_thumbnail_maintains_aspect_ratio(self, temp_dir):
        """Test that thumbnail maintains aspect ratio."""
        # Create source image (9:16 aspect ratio)
        img = Image.new("RGB", (1080, 1920), color=(100, 150, 200))
        thumbnail_path = temp_dir / "thumb.jpg"

        create_thumbnail_from_image(img, thumbnail_path)

        thumb = Image.open(thumbnail_path)
        # Check aspect ratio is preserved (9:16 = 0.5625)
        aspect_ratio = thumb.size[0] / thumb.size[1]
        expected_ratio = 1080 / 1920
        assert abs(aspect_ratio - expected_ratio) < 0.01

    def test_create_thumbnail_custom_size(self, temp_dir):
        """Test thumbnail with custom max size."""
        img = Image.new("RGB", (1080, 1920), color=(100, 150, 200))
        thumbnail_path = temp_dir / "thumb.jpg"

        create_thumbnail_from_image(
            img, thumbnail_path, max_size=(320, 569)
        )

        thumb = Image.open(thumbnail_path)
        assert thumb.size[0] <= 320
        assert thumb.size[1] <= 569

    def test_create_thumbnail_creates_parent_dir(self):
        """Test that parent directory is created if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            thumbnail_path = Path(tmpdir) / "subdir" / "thumb.jpg"
            assert not thumbnail_path.parent.exists()

            img = Image.new("RGB", (1080, 1920), color=(100, 150, 200))
            create_thumbnail_from_image(img, thumbnail_path)

            assert thumbnail_path.parent.exists()
            assert thumbnail_path.exists()

    def test_create_thumbnail_jpeg_format(self, temp_dir):
        """Test that thumbnail is saved as JPEG."""
        img = Image.new("RGB", (1080, 1920), color=(100, 150, 200))
        thumbnail_path = temp_dir / "thumb.jpg"

        create_thumbnail_from_image(img, thumbnail_path)

        # Verify it's a valid JPEG
        thumb = Image.open(thumbnail_path)
        assert thumb.format == "JPEG"
