"""Image generation utilities for E-type video backgrounds.

This module provides helper functions for creating background images for
fictional concept videos using PIL (Pillow).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from reelsbot.models import ReelPlan

# Category-specific background colors (RGB tuples)
CATEGORY_COLORS: dict[str, tuple[int, int, int]] = {
    "cafe": (245, 240, 235),        # Warm beige
    "packaging": (250, 250, 255),   # Cool white
    "poster": (240, 245, 250),      # Light blue
    "app_ui": (248, 248, 252),      # Neutral gray
    "product_design": (252, 248, 243),  # Cream
    "place_concept": (238, 242, 245),   # Light steel blue
}

# Default background color for unknown categories
DEFAULT_BG_COLOR: tuple[int, int, int] = (245, 245, 250)

# Standard Instagram Reel dimensions (9:16 aspect ratio)
REEL_WIDTH: int = 1080
REEL_HEIGHT: int = 1920


def create_concept_background(plan: ReelPlan, temp_dir: Path) -> Path:
    """Generate a PIL image background for E-type fictional concept videos.

    Creates a simple, clean background image with:
    - Category-specific background color
    - Brand name (center, large font)
    - Concept title (below brand name, smaller font)
    - Minimal geometric shape representing the category

    Args:
        plan: ReelPlan with E-type content details (brand_name, concept_title, category).
        temp_dir: Directory to save the temporary background image.

    Returns:
        Path to the generated background image (PNG format).

    Raises:
        ValueError: If plan is not E-type or missing required fields.

    Example:
        >>> plan = ReelPlan(
        ...     type="E",
        ...     theme="cafe",
        ...     mood="calm",
        ...     duration_sec=12,
        ...     brand_name="ZENITH",
        ...     concept_title="Modern Cafe Interior",
        ...     category="cafe"
        ... )
        >>> bg_path = create_concept_background(plan, Path("/tmp"))
        >>> print(f"Background saved to: {bg_path}")
    """
    if not plan.is_educational():
        raise ValueError("create_concept_background requires E-type plan")

    if not plan.brand_name or not plan.concept_title or not plan.category:
        raise ValueError(
            "E-type plan must have brand_name, concept_title, and category"
        )

    # Create image with category-specific background color
    bg_color = CATEGORY_COLORS.get(plan.category, DEFAULT_BG_COLOR)
    img = Image.new("RGB", (REEL_WIDTH, REEL_HEIGHT), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Add minimal geometric shape based on category
    _add_category_shape(draw, plan.category, bg_color)

    # Add brand name (center, large)
    brand_y = REEL_HEIGHT // 2 - 100
    add_text_to_image(
        img=img,
        text=plan.brand_name,
        position=(REEL_WIDTH // 2, brand_y),
        font_size=84,
        color=(40, 40, 45),  # Dark gray
        bold=True,
        align="center",
    )

    # Add concept title (below brand, smaller)
    concept_y = brand_y + 150
    add_text_to_image(
        img=img,
        text=plan.concept_title,
        position=(REEL_WIDTH // 2, concept_y),
        font_size=42,
        color=(80, 80, 85),  # Medium gray
        bold=False,
        align="center",
    )

    # Save to temp file
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / f"bg_{plan.brand_name.lower().replace(' ', '_')}.png"
    img.save(output_path, "PNG")

    return output_path


def add_text_to_image(
    img: Image.Image,
    text: str,
    position: tuple[int, int],
    font_size: int,
    color: tuple[int, int, int],
    bold: bool = False,
    align: str = "left",
) -> Image.Image:
    """Draw text on a PIL image with specified styling.

    Args:
        img: PIL Image to draw on.
        text: Text string to render.
        position: (x, y) coordinates for text placement.
        font_size: Font size in pixels.
        color: RGB color tuple (e.g., (255, 255, 255) for white).
        bold: Whether to use bold font (default: False).
        align: Text alignment - "left", "center", or "right" (default: "left").

    Returns:
        The modified PIL Image (modified in-place).

    Example:
        >>> img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))
        >>> add_text_to_image(
        ...     img=img,
        ...     text="Hello World",
        ...     position=(540, 960),
        ...     font_size=48,
        ...     color=(0, 0, 0),
        ...     bold=True,
        ...     align="center"
        ... )
    """
    draw = ImageDraw.Draw(img)

    # Try to load Arial font (Windows standard)
    font = _load_font(font_size, bold)

    # Get text bounding box for alignment
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Adjust position based on alignment
    x, y = position
    if align == "center":
        x = x - text_width // 2
    elif align == "right":
        x = x - text_width

    # Draw text
    draw.text((x, y), text, font=font, fill=color)

    return img


def _load_font(font_size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Arial font with fallback to default font.

    Args:
        font_size: Font size in pixels.
        bold: Whether to load bold variant.

    Returns:
        ImageFont.FreeTypeFont instance.
    """
    # Try Windows Arial font first
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, font_size)
        except OSError:
            continue

    # Fallback to default font
    return ImageFont.load_default()


def _add_category_shape(
    draw: ImageDraw.ImageDraw,
    category: str,
    bg_color: tuple[int, int, int],
) -> None:
    """Add a minimal geometric shape to represent the category.

    Args:
        draw: ImageDraw instance.
        category: Category name (cafe, packaging, poster, etc.).
        bg_color: Background color for contrast calculation.
    """
    # Calculate a slightly darker shade for the shape
    shape_color = tuple(max(0, c - 20) for c in bg_color)

    # Define shapes for each category
    if category == "cafe":
        # Coffee cup outline (simple rectangle with circle)
        draw.rectangle(
            [(REEL_WIDTH // 2 - 60, 300), (REEL_WIDTH // 2 + 60, 450)],
            outline=shape_color,
            width=3,
        )
        draw.ellipse(
            [(REEL_WIDTH // 2 - 60, 280), (REEL_WIDTH // 2 + 60, 320)],
            outline=shape_color,
            width=3,
        )

    elif category == "packaging":
        # Box/package outline
        draw.rectangle(
            [(REEL_WIDTH // 2 - 80, 280), (REEL_WIDTH // 2 + 80, 460)],
            outline=shape_color,
            width=3,
        )
        draw.line(
            [(REEL_WIDTH // 2 - 80, 370), (REEL_WIDTH // 2 + 80, 370)],
            fill=shape_color,
            width=3,
        )

    elif category == "poster":
        # Frame/border shape
        draw.rectangle(
            [(REEL_WIDTH // 2 - 100, 260), (REEL_WIDTH // 2 + 100, 480)],
            outline=shape_color,
            width=4,
        )

    elif category == "app_ui":
        # Mobile phone outline
        draw.rounded_rectangle(
            [(REEL_WIDTH // 2 - 50, 280), (REEL_WIDTH // 2 + 50, 460)],
            radius=15,
            outline=shape_color,
            width=3,
        )
        draw.rectangle(
            [(REEL_WIDTH // 2 - 15, 440), (REEL_WIDTH // 2 + 15, 445)],
            fill=shape_color,
        )

    elif category == "product_design":
        # Abstract product shape (circle + triangle)
        draw.ellipse(
            [(REEL_WIDTH // 2 - 60, 300), (REEL_WIDTH // 2 + 60, 420)],
            outline=shape_color,
            width=3,
        )

    elif category == "place_concept":
        # Building/structure outline
        draw.polygon(
            [
                (REEL_WIDTH // 2, 280),
                (REEL_WIDTH // 2 - 80, 380),
                (REEL_WIDTH // 2 + 80, 380),
            ],
            outline=shape_color,
            width=3,
        )
        draw.rectangle(
            [(REEL_WIDTH // 2 - 80, 380), (REEL_WIDTH // 2 + 80, 470)],
            outline=shape_color,
            width=3,
        )

    else:
        # Default: simple circle
        draw.ellipse(
            [(REEL_WIDTH // 2 - 70, 300), (REEL_WIDTH // 2 + 70, 440)],
            outline=shape_color,
            width=3,
        )


def create_thumbnail_from_image(
    img: Image.Image,
    thumbnail_path: Path,
    max_size: tuple[int, int] = (640, 1138),
) -> Path:
    """Create a thumbnail from a PIL image.

    Args:
        img: Source PIL Image.
        thumbnail_path: Path to save thumbnail.
        max_size: Maximum thumbnail dimensions (width, height).

    Returns:
        Path to the saved thumbnail.

    Example:
        >>> img = Image.open("background.png")
        >>> thumb_path = create_thumbnail_from_image(img, Path("thumb.jpg"))
    """
    # Create thumbnail (maintains aspect ratio)
    img_copy = img.copy()
    img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Save as JPEG
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    img_copy.save(thumbnail_path, "JPEG", quality=90)

    return thumbnail_path
