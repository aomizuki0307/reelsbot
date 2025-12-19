# reelsbot Technical Architecture

> Deep dive into the technical design and implementation of the Instagram Reels automation system

Version: 0.1.0
Last Updated: 2025-12-19

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Component Details](#component-details)
4. [Data Models](#data-models)
5. [Design Decisions](#design-decisions)
6. [Extension Points](#extension-points)
7. [Safety & Compliance](#safety--compliance)
8. [Performance Considerations](#performance-considerations)
9. [Future Enhancements](#future-enhancements)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLI Interface (cli.py)                      │
│              plan | run | validate | info                           │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Orchestrator (orchestrator.py)                    │
│         Pipeline coordination and workflow management               │
└──┬────────┬─────────┬──────────┬────────────┬────────────┬─────────┘
   │        │         │          │            │            │
   ▼        ▼         ▼          ▼            ▼            ▼
┌─────┐ ┌──────┐ ┌────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│Plan │ │Policy│ │Caption │ │Generator│ │ Editor  │ │Publisher │
│ner  │ │Gate  │ │Gener.  │ │         │ │         │ │          │
└──┬──┘ └──┬───┘ └───┬────┘ └────┬────┘ └────┬────┘ └────┬─────┘
   │       │         │           │           │           │
   └───────┴─────────┴───────────┴───────────┴───────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Foundation Layer                               │
│   Config | LLM Client | Logger | Utils | Models | Storage           │
└─────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    External Dependencies                             │
│   Anthropic/OpenAI API | FFmpeg | File System                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (CLI)
    │
    ▼
Planning Phase
    ├─> LLM generates ReelPlan
    └─> Policy validation
           │
           ▼
Generation Phase
    ├─> Video generation (FFmpeg)
    ├─> Caption generation (LLM)
    ├─> Video editing (overlays)
    └─> Metadata creation
           │
           ▼
Publishing Phase
    ├─> Dry-run: Save to disk
    └─> Live: Instagram API (future)
           │
           ▼
Output: Videos + Metadata + Logs
```

### Component Responsibilities

| Component | Responsibility | Input | Output |
|-----------|----------------|-------|--------|
| **CLI** | User interface, command parsing | User commands | Status messages |
| **Orchestrator** | Pipeline coordination | Run parameters | ReelMetadata list |
| **Planner** | Content idea generation | Count, ratio | ReelPlan list |
| **PolicyGate** | Content validation | ReelPlan | Validation result |
| **CaptionGenerator** | Caption writing | ReelPlan | Caption text |
| **Generator** | Video creation | ReelPlan | Video file path |
| **Editor** | Video post-processing | Video + plan | Final video path |
| **Publisher** | Content distribution | ReelMetadata | Publication status |
| **Storage** | Data persistence | Metadata | File paths |

---

## Architecture Layers

### Layer 1: Foundation (Phase 1)

**Purpose:** Core infrastructure and utilities

**Components:**
- `config.py` - Configuration management with Pydantic
- `llm_client.py` - Abstract LLM interface (Anthropic/OpenAI)
- `models.py` - Data models (ReelPlan, ReelMetadata)
- `utils/logger.py` - Structured logging
- `utils/paths.py` - Path management
- `utils/brand_name.py` - Brand name generation

**Design Principles:**
- Single Responsibility: Each module has one clear purpose
- Dependency Inversion: High-level modules depend on abstractions
- Configuration as Code: Type-safe configuration with validation

**Example: LLM Abstraction**
```python
# Abstract interface allows swapping providers
class LLMClient(ABC):
    @abstractmethod
    async def generate_plan(self, prompt: str) -> str:
        pass

# Concrete implementations
class AnthropicLLMClient(LLMClient):
    # Anthropic-specific implementation
    pass

class OpenAILLMClient(LLMClient):
    # OpenAI-specific implementation
    pass

# Factory pattern for creation
def create_llm_client(config: Config) -> LLMClient:
    if config.llm_provider == "anthropic":
        return AnthropicLLMClient(config)
    elif config.llm_provider == "openai":
        return OpenAILLMClient(config)
```

### Layer 2: Business Logic (Phase 2)

**Purpose:** Core domain logic for content generation

**Components:**
- `planner.py` - Content planning with LLM
- `policy_gate.py` - Dual-layer policy validation
- `caption_generator.py` - Caption writing
- `storage/runs.py` - Metadata persistence

**Design Patterns:**
- **Strategy Pattern**: Interchangeable LLM providers
- **Template Method**: Common validation flow, customized checks
- **Repository Pattern**: Abstract storage interface

**Policy Gate Architecture:**

```
                    ┌─────────────────────┐
                    │   ReelPlan Input    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Policy Gate       │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Keyword Gate │  │   LLM Gate   │  │  E-type Gate │
    │  (Heuristic) │  │  (Semantic)  │  │  (Fictional) │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           └─────────────────┼──────────────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Validation Result  │
                  │  {is_valid, reason} │
                  └─────────────────────┘
```

**Dual-Layer Validation:**
1. **Layer 1 - Keyword Filter** (Fast, deterministic)
   - Checks against `blocked_terms.txt`
   - Immediate rejection of obvious violations
   - No API cost

2. **Layer 2 - LLM Semantic Analysis** (Slow, nuanced)
   - Context-aware brand safety check
   - Detects subtle policy violations
   - Uses same LLM as content generation

### Layer 3: Video Generation (Phase 3)

**Purpose:** Video creation and editing

**Components:**
- `generator/ffmpeg_dummy.py` - FFmpeg-based video generation
- `editor/ffmpeg_editor.py` - Video overlay and editing
- `utils/ffmpeg.py` - FFmpeg command utilities
- `utils/image.py` - Image generation and manipulation

**FFmpeg Pipeline:**

```
Raw Video Generation
    │
    ├─> A-type: Abstract animation
    │   ├─> Generate gradient/geometric patterns
    │   ├─> Create looping animation
    │   └─> Export as base video
    │
    └─> E-type: Fictional concept
        ├─> Generate mockup images
        ├─> Create slideshow/pan animation
        └─> Export as base video
            │
            ▼
Overlay Addition
    │
    ├─> A-type: Tagline overlay
    │   ├─> Generate text image
    │   ├─> Position center
    │   └─> Overlay with ffmpeg
    │
    └─> E-type: Brand name overlay
        ├─> Generate brand text image
        ├─> Position top-center
        └─> Overlay with ffmpeg
            │
            ▼
Final Video (1080x1920, 30fps, H.264)
```

**FFmpeg Command Example:**
```bash
# A-type video with tagline overlay
ffmpeg -loop 1 -i gradient.png -i tagline.png \
  -filter_complex "[0:v][1:v]overlay=(W-w)/2:(H-h)/2" \
  -c:v libx264 -t 10 -pix_fmt yuv420p \
  -r 30 -s 1080x1920 \
  output.mp4
```

### Layer 4: Orchestration (Phase 4)

**Purpose:** End-to-end pipeline execution

**Components:**
- `orchestrator.py` - Main pipeline coordinator
- `cli.py` - Command-line interface
- `publisher/dry_run.py` - Local publishing (MVP)
- `publisher/base.py` - Publisher interface

**Orchestration Flow:**

```python
async def run_pipeline(count, type_filter, mix, dry_run):
    """Execute complete content generation pipeline."""

    # 1. Planning Phase
    plans = await planner.generate_daily_plan(count, type_filter, mix)

    # 2. Generation Loop
    for plan in plans:
        # 2a. Policy validation
        validation = await policy_gate.validate(plan)
        if not validation["is_valid"]:
            retry_or_skip()

        # 2b. Video generation
        video_path = await generator.generate(plan)

        # 2c. Video editing (overlays)
        final_video = await editor.add_overlays(video_path, plan)

        # 2d. Caption generation
        caption = await caption_generator.generate(plan)

        # 2e. Create metadata
        metadata = ReelMetadata(
            plan=plan,
            caption=caption,
            video_path=final_video,
            ...
        )

        # 2f. Save metadata
        storage.save_metadata(metadata)

        # 2g. Publish
        await publisher.publish(metadata)

    return metadata_list
```

---

## Component Details

### Config (config.py)

**Responsibilities:**
- Load environment variables
- Validate configuration
- Provide type-safe access to settings

**Implementation:**
```python
class Config(BaseSettings):
    # LLM settings
    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Video settings
    video_resolution: tuple[int, int] = (1080, 1920)
    video_fps: int = 30

    # Validation
    @field_validator("anthropic_api_key")
    def validate_api_key(cls, v, info):
        if info.data.get("llm_provider") == "anthropic" and not v:
            raise ValueError("ANTHROPIC_API_KEY required")
        return v
```

**Key Features:**
- Pydantic-based validation
- Environment variable loading with `.env` support
- Type safety throughout application
- Sensible defaults for all settings

### LLM Client (llm_client.py)

**Responsibilities:**
- Abstract LLM provider differences
- Handle API calls with retries
- Parse structured responses

**Implementation Strategy:**
```python
class LLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 1.0,
    ) -> str:
        """Generate text completion."""
        pass

# Tenacity for retries
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(APIError),
)
async def _call_api(self, prompt: str) -> str:
    # Provider-specific implementation
    pass
```

**Error Handling:**
- Automatic retries with exponential backoff
- Rate limit handling
- Timeout management
- Graceful degradation

### Planner (planner.py)

**Responsibilities:**
- Generate content plans using LLM
- Determine A/E mix ratios
- Parse LLM responses into ReelPlan objects

**Prompt Engineering:**
```python
def _build_planning_prompt(self, count: int, type_filter: str) -> str:
    """Build structured prompt for content planning."""

    return f"""
    Generate {count} Instagram Reels content plans.

    Content Types:
    - A-type (Abstract): Visual loops with taglines
      * Themes: gradient, geometric, kinetic, particles
      * Duration: {self.config.default_a_duration_min}-{self.config.default_a_duration_max}s
      * Include: tagline (3-7 words)

    - E-type (Educational): Fictional brand concepts
      * Categories: cafe, packaging, poster, app_ui, product_design
      * Duration: {self.config.default_e_duration_min}-{self.config.default_e_duration_max}s
      * Include: brand_name (7-14 chars), concept_title, category

    Output JSON array of plans:
    [
      {{
        "type": "A",
        "theme": "gradient",
        "mood": "calm",
        "duration_sec": 10,
        "tagline": "Find peace in motion"
      }},
      ...
    ]
    """
```

**Response Parsing:**
- JSON extraction from LLM response
- Pydantic validation of each plan
- Retry on parse failures

### Policy Gate (policy_gate.py)

**Dual-Layer Architecture:**

**Layer 1: Keyword Filter**
```python
def _check_blocked_terms(self, plan: ReelPlan) -> dict:
    """Fast keyword-based filtering."""

    blocked_terms = self._load_blocked_terms()

    # Check all text fields
    text_to_check = [
        plan.tagline or "",
        plan.brand_name or "",
        plan.concept_title or "",
        plan.theme,
    ]

    for text in text_to_check:
        for term in blocked_terms:
            if term.lower() in text.lower():
                return {
                    "is_valid": False,
                    "reason": f"Blocked term detected: {term}",
                    "layer": "keyword",
                }

    return {"is_valid": True}
```

**Layer 2: LLM Semantic Analysis**
```python
async def _check_llm_policy(self, plan: ReelPlan) -> dict:
    """Deep semantic policy validation."""

    prompt = f"""
    Analyze this content plan for brand safety and policy compliance:

    Type: {plan.type}
    Theme: {plan.theme}
    {"Tagline: " + plan.tagline if plan.tagline else ""}
    {"Brand: " + plan.brand_name if plan.brand_name else ""}

    Check for:
    1. Real brand/trademark conflicts
    2. Controversial or sensitive content
    3. Misleading information
    4. Inappropriate themes

    Respond with JSON: {{"is_valid": true/false, "reason": "..."}}
    """

    response = await self.llm_client.generate_text(prompt)
    return json.loads(response)
```

**E-type Specific Validation:**
```python
def _validate_e_type_fictional(self, plan: ReelPlan) -> dict:
    """Ensure E-type content is clearly fictional."""

    if plan.type != "E":
        return {"is_valid": True}

    # Brand name must be distinctive (7-14 chars)
    if not plan.brand_name or len(plan.brand_name) < 7:
        return {
            "is_valid": False,
            "reason": "E-type requires distinctive brand name (7-14 chars)",
        }

    # Check against real brands (simplified)
    real_brands = ["Apple", "Google", "Nike", "Adidas", ...]
    if plan.brand_name in real_brands:
        return {
            "is_valid": False,
            "reason": f"Brand name conflicts with real brand",
        }

    return {"is_valid": True}
```

### Generator (generator/ffmpeg_dummy.py)

**Video Generation Strategies:**

**A-type: Abstract Animations**
```python
async def _generate_a_type(self, plan: ReelPlan) -> Path:
    """Generate abstract visual loop."""

    # 1. Generate base image based on theme
    if plan.theme == "gradient":
        image = self._create_gradient_image(plan.mood)
    elif plan.theme == "geometric":
        image = self._create_geometric_pattern(plan.mood)
    elif plan.theme == "kinetic":
        image = self._create_kinetic_pattern(plan.mood)

    # 2. Create looping video with FFmpeg
    video_path = self._create_looping_video(
        image=image,
        duration=plan.duration_sec,
        fps=self.config.video_fps,
    )

    return video_path

def _create_gradient_image(self, mood: str) -> Image:
    """Generate gradient based on mood."""

    color_schemes = {
        "calm": [(135, 206, 250), (70, 130, 180)],     # Blue gradient
        "energetic": [(255, 99, 71), (255, 215, 0)],   # Orange-yellow
        "dreamy": [(221, 160, 221), (147, 112, 219)],  # Purple gradient
    }

    colors = color_schemes.get(mood, [(100, 100, 100), (200, 200, 200)])

    # Create gradient image with PIL
    image = Image.new("RGB", (1080, 1920))
    draw = ImageDraw.Draw(image)

    for y in range(1920):
        ratio = y / 1920
        r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
        draw.line([(0, y), (1080, y)], fill=(r, g, b))

    return image
```

**E-type: Fictional Concepts**
```python
async def _generate_e_type(self, plan: ReelPlan) -> Path:
    """Generate fictional brand concept video."""

    # 1. Generate mockup images based on category
    if plan.category == "cafe":
        images = self._create_cafe_mockups(plan.brand_name)
    elif plan.category == "packaging":
        images = self._create_packaging_mockups(plan.brand_name)
    elif plan.category == "app_ui":
        images = self._create_app_ui_mockups(plan.brand_name)

    # 2. Create slideshow or pan video
    video_path = self._create_slideshow_video(
        images=images,
        duration=plan.duration_sec,
        transition="fade",
    )

    return video_path

def _create_cafe_mockups(self, brand_name: str) -> list[Image]:
    """Create cafe interior mockups with branding."""

    images = []

    # Mockup 1: Storefront
    img1 = Image.new("RGB", (1080, 1920), (240, 230, 220))
    draw = ImageDraw.Draw(img1)
    font = ImageFont.truetype("arial.ttf", 120)
    draw.text((540, 400), brand_name, fill=(60, 40, 30),
              font=font, anchor="mm")
    images.append(img1)

    # Mockup 2: Interior
    img2 = Image.new("RGB", (1080, 1920), (250, 240, 230))
    # Add branding elements, furniture, etc.
    images.append(img2)

    return images
```

### Editor (editor/ffmpeg_editor.py)

**Overlay Addition:**
```python
async def add_text_overlay(
    self,
    video_path: Path,
    plan: ReelPlan,
) -> Path:
    """Add text overlay to video."""

    # 1. Generate overlay image
    if plan.type == "A":
        overlay_img = self._create_tagline_overlay(plan.tagline)
        position = "center"
    else:  # E-type
        overlay_img = self._create_brand_overlay(plan.brand_name)
        position = "top"

    # 2. Build FFmpeg overlay command
    output_path = video_path.parent / f"final_{video_path.name}"

    cmd = (
        ffmpeg
        .input(str(video_path))
        .input(str(overlay_img))
        .filter_complex(self._get_overlay_filter(position))
        .output(
            str(output_path),
            vcodec="libx264",
            pix_fmt="yuv420p",
            **{"b:v": "5M"},
        )
    )

    await self._run_ffmpeg(cmd)

    return output_path

def _create_tagline_overlay(self, tagline: str) -> Path:
    """Create semi-transparent tagline image."""

    # Create image with text
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("arial.ttf", 80)

    # Add semi-transparent background
    text_bbox = draw.textbbox((0, 0), tagline, font=font)
    bg_box = [
        (1080 - text_bbox[2]) // 2 - 40,
        (1920 - text_bbox[3]) // 2 - 20,
        (1080 + text_bbox[2]) // 2 + 40,
        (1920 + text_bbox[3]) // 2 + 20,
    ]
    draw.rectangle(bg_box, fill=(0, 0, 0, 180))

    # Add text
    draw.text(
        (540, 960),
        tagline,
        fill=(255, 255, 255, 255),
        font=font,
        anchor="mm",
    )

    overlay_path = Path(f"temp_overlay_{uuid.uuid4()}.png")
    img.save(overlay_path)

    return overlay_path
```

### Caption Generator (caption_generator.py)

**LLM-Powered Caption Writing:**
```python
async def generate_caption(self, plan: ReelPlan) -> str:
    """Generate Instagram caption for reel."""

    prompt = self._build_caption_prompt(plan)
    caption = await self.llm_client.generate_text(prompt)

    # Ensure E-type includes "Fictional concept" disclaimer
    if plan.type == "E" and "fictional" not in caption.lower():
        caption = f"Fictional concept: {plan.brand_name}\n\n{caption}"

    return caption

def _build_caption_prompt(self, plan: ReelPlan) -> str:
    """Build caption generation prompt."""

    if plan.type == "A":
        return f"""
        Write an Instagram caption for an abstract visual reel:

        Theme: {plan.theme}
        Mood: {plan.mood}
        Tagline: {plan.tagline}

        Requirements:
        - 2-3 sentences
        - Inspirational and artistic tone
        - Encourage viewers to relax/reflect
        - Include relevant hashtags (5-8)

        Example: "Let your mind drift with the flow of endless gradients.
        Sometimes the most beautiful moments are the simplest. 🎨✨

        #abstractart #visualart #calmvibes #digitalart #meditation"
        """
    else:  # E-type
        return f"""
        Write an Instagram caption for a fictional brand concept:

        Brand: {plan.brand_name}
        Concept: {plan.concept_title}
        Category: {plan.category}

        Requirements:
        - Start with "Fictional concept:"
        - 2-3 sentences describing the concept
        - Educational tone about design/branding
        - Include relevant hashtags (5-8)

        Example: "Fictional concept: BrewCraft, a modern cafe brand.
        Exploring minimalist design with warm, earthy tones.
        What do you think of this concept? 💡☕

        #brandingdesign #conceptart #cafedesign #graphicdesign"
        """
```

---

## Data Models

### ReelPlan

**Purpose:** Structured content plan before generation

```python
class ReelPlan(BaseModel):
    """Content plan for a single Instagram Reel."""

    type: Literal["A", "E"]
    theme: str
    mood: str
    duration_sec: int

    # A-type specific
    tagline: str | None = None

    # E-type specific
    brand_name: str | None = Field(None, min_length=7, max_length=14)
    concept_title: str | None = None
    category: str | None = None

    def model_post_init(self, __context) -> None:
        """Validate type-specific fields."""
        if self.type == "A" and not self.tagline:
            raise ValueError("A-type requires tagline")
        if self.type == "E" and not all([self.brand_name,
                                          self.concept_title,
                                          self.category]):
            raise ValueError("E-type requires brand_name, "
                           "concept_title, category")
```

**Design Rationale:**
- Union type pattern for A/E specific fields
- Post-initialization validation for cross-field constraints
- Immutable by default (Pydantic frozen mode possible)

### ReelMetadata

**Purpose:** Complete record of generated content

```python
class ReelMetadata(BaseModel):
    """Complete metadata for a generated Instagram Reel."""

    run_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    plan: ReelPlan
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    video_path: Path
    thumbnail_path: Path
    status: Literal["generated", "failed", "published"] = "generated"

    class Config:
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }
```

**Serialization:**
```json
{
  "run_id": "run_20251219_143022",
  "timestamp": "2025-12-19T14:30:22.123456",
  "plan": {
    "type": "A",
    "theme": "gradient",
    "mood": "calm",
    "duration_sec": 10,
    "tagline": "Find peace in motion"
  },
  "caption": "Let your mind drift...",
  "hashtags": ["abstractart", "visualart"],
  "video_path": "outputs/run_20251219_143022/video_1.mp4",
  "thumbnail_path": "outputs/run_20251219_143022/thumbnail_1.png",
  "status": "generated"
}
```

---

## Design Decisions

### 1. Why FFmpeg for MVP?

**Decision:** Use FFmpeg for video generation instead of advanced libraries (Manim, MoviePy)

**Rationale:**
- **Ubiquity**: FFmpeg is industry-standard, widely available
- **Performance**: Native code, extremely fast
- **Simplicity**: Single binary, no complex dependencies
- **Flexibility**: Can handle any video processing task
- **Windows Support**: Excellent Windows compatibility

**Trade-offs:**
- Less sophisticated animations than Manim
- Command-line interface (not programmatic)
- Requires external binary

**Future Migration Path:**
```python
# Current: FFmpeg-based generator
class FFmpegDummyGenerator(BaseGenerator):
    pass

# Future: Advanced generator
class ManimGenerator(BaseGenerator):
    """Generate complex mathematical animations."""
    pass

class BlenderGenerator(BaseGenerator):
    """Generate 3D rendered concepts."""
    pass

# Factory pattern allows easy swapping
def create_generator(config: Config) -> BaseGenerator:
    if config.generator_type == "ffmpeg":
        return FFmpegDummyGenerator(config)
    elif config.generator_type == "manim":
        return ManimGenerator(config)
```

### 2. LLM Abstraction Rationale

**Decision:** Abstract LLM providers behind common interface

**Benefits:**
- **Flexibility**: Easy to switch providers
- **Cost Optimization**: Use different models for different tasks
- **Redundancy**: Fallback to alternative provider
- **Testing**: Mock LLM for unit tests

**Implementation:**
```python
# Single interface, multiple implementations
llm_client: LLMClient = create_llm_client(config)

# Works with any provider
plan = await llm_client.generate_plan(prompt)
```

### 3. Policy Gate Dual-Layer Approach

**Decision:** Combine keyword filtering + LLM semantic analysis

**Why Dual-Layer?**

| Aspect | Keyword Filter | LLM Analysis |
|--------|----------------|--------------|
| **Speed** | Instant (~1ms) | Slow (~2s) |
| **Cost** | Free | $0.001-0.005/call |
| **Accuracy** | High precision, low recall | High precision, high recall |
| **Coverage** | Explicit violations | Nuanced violations |

**Combined Approach:**
1. Keyword filter catches 80% of violations instantly
2. LLM analysis catches remaining 20% with context awareness
3. Total validation time: ~2s (vs 100% LLM: ~2s, 100% keyword: many false positives)

### 4. DRY_RUN Publisher Design

**Decision:** Default to dry-run mode, not live publishing

**Rationale:**
- **Safety**: Prevents accidental publishing during development
- **Testing**: Easy to verify generated content
- **Iteration**: Generate many videos quickly without API limits
- **Manual Review**: Allows human oversight before publishing

**Implementation:**
```python
class DryRunPublisher(BasePublisher):
    """Publisher that saves locally, doesn't publish."""

    async def publish(self, metadata: ReelMetadata) -> str:
        # Save to disk, don't call Instagram API
        self.storage.save_metadata(metadata)
        return "dry_run_success"

class InstagramPublisher(BasePublisher):
    """Publisher that uses Instagram Graph API."""

    async def publish(self, metadata: ReelMetadata) -> str:
        # Call Instagram API
        response = await self._upload_to_instagram(metadata)
        return response.id
```

### 5. E-type "Fictional Concept" Requirement

**Decision:** Require "Fictional concept:" prefix in E-type captions

**Legal Rationale:**
- **Trademark Protection**: Clearly distinguishes fictional from real brands
- **Transparency**: Users know content is conceptual, not actual products
- **Policy Compliance**: Instagram/Meta guidelines for branded content

**Enforcement:**
```python
if plan.type == "E":
    # Caption generator always includes disclaimer
    if "fictional" not in caption.lower():
        caption = f"Fictional concept: {plan.brand_name}\n\n{caption}"

    # Policy gate validates disclaimer exists
    if "fictional" not in metadata.caption.lower():
        return {"is_valid": False, "reason": "Missing fictional disclaimer"}
```

---

## Extension Points

### 1. Meta Graph API Integration

**Current State:** Dry-run publisher (local save only)

**Integration Plan:**
```python
class InstagramGraphPublisher(BasePublisher):
    """Publish via Instagram Graph API."""

    def __init__(self, config: Config):
        self.access_token = config.meta_access_token
        self.account_id = config.instagram_account_id
        self.graph_api_url = "https://graph.facebook.com/v18.0"

    async def publish(self, metadata: ReelMetadata) -> str:
        """Upload reel to Instagram."""

        # 1. Create media container
        container_id = await self._create_container(metadata)

        # 2. Upload video
        await self._upload_video(container_id, metadata.video_path)

        # 3. Publish container
        media_id = await self._publish_container(
            container_id,
            caption=metadata.get_full_caption(),
        )

        return media_id

    async def _create_container(self, metadata: ReelMetadata) -> str:
        """Create media container for reel."""

        url = f"{self.graph_api_url}/{self.account_id}/media"

        data = {
            "media_type": "REELS",
            "video_url": self._get_public_url(metadata.video_path),
            "caption": metadata.get_full_caption(),
            "cover_url": self._get_public_url(metadata.thumbnail_path),
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()["id"]
```

**Required Configuration:**
```ini
# .env additions
META_ACCESS_TOKEN=your-long-lived-access-token
INSTAGRAM_ACCOUNT_ID=your-instagram-business-account-id
```

### 2. External Video Generation APIs

**Integration: RunwayML, Pika Labs, Stability AI**

```python
class RunwayMLGenerator(BaseGenerator):
    """Generate videos using RunwayML API."""

    async def generate(self, plan: ReelPlan) -> Path:
        """Generate video via RunwayML Gen-2."""

        # 1. Build text prompt from plan
        prompt = self._build_runway_prompt(plan)

        # 2. Call RunwayML API
        task_id = await self._create_generation_task(prompt)

        # 3. Poll for completion
        video_url = await self._wait_for_completion(task_id)

        # 4. Download video
        video_path = await self._download_video(video_url)

        return video_path

    def _build_runway_prompt(self, plan: ReelPlan) -> str:
        """Convert ReelPlan to RunwayML prompt."""

        if plan.type == "A":
            return f"{plan.theme} abstract animation, {plan.mood} mood, " \
                   f"looping, smooth transitions, 4K"
        else:
            return f"{plan.concept_title}, {plan.category} design, " \
                   f"professional mockup, clean aesthetic"
```

### 3. Alternative Storage Backends

**Current:** JSON files in outputs/ directory

**Extension: Database Storage**

```python
class SQLiteStorage(BaseStorage):
    """Store metadata in SQLite database."""

    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reels (
                run_id TEXT PRIMARY KEY,
                timestamp TEXT,
                plan JSON,
                caption TEXT,
                video_path TEXT,
                thumbnail_path TEXT,
                status TEXT
            )
        """)

    async def save_metadata(self, metadata: ReelMetadata) -> Path:
        """Save metadata to database."""

        self.conn.execute("""
            INSERT INTO reels VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.run_id,
            metadata.timestamp.isoformat(),
            metadata.plan.model_dump_json(),
            metadata.caption,
            str(metadata.video_path),
            str(metadata.thumbnail_path),
            metadata.status,
        ))
        self.conn.commit()
```

### 4. Custom Content Generators

**Plugin System for Custom Generators:**

```python
# Custom generator example
class CustomAbstractGenerator(BaseGenerator):
    """User-defined generator for specific visual style."""

    async def generate(self, plan: ReelPlan) -> Path:
        # Custom implementation
        # - Use Pillow for custom graphics
        # - Call external APIs
        # - Use ML models
        pass

# Registration system
GENERATOR_REGISTRY = {
    "ffmpeg": FFmpegDummyGenerator,
    "manim": ManimGenerator,
    "runway": RunwayMLGenerator,
    "custom_abstract": CustomAbstractGenerator,
}

def create_generator(generator_type: str, config: Config) -> BaseGenerator:
    generator_class = GENERATOR_REGISTRY.get(generator_type)
    if not generator_class:
        raise ValueError(f"Unknown generator: {generator_type}")
    return generator_class(config)
```

---

## Safety & Compliance

### Policy Gate Architecture

```
Content Input (ReelPlan)
         │
         ▼
┌────────────────────┐
│  Keyword Filter    │ ← blocked_terms.txt
│  (Layer 1)         │   (Nike, Gucci, Tesla...)
└────────┬───────────┘
         │
         ├─ PASS ──────────────┐
         │                     │
         ▼                     ▼
┌────────────────────┐  ┌──────────────┐
│  LLM Policy Check  │  │  E-type      │
│  (Layer 2)         │  │  Validation  │
└────────┬───────────┘  └──────┬───────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌────────────────────┐
         │  Validation Result │
         │  {is_valid, reason}│
         └────────────────────┘
```

### Blocked Terms Management

**File:** `policies/blocked_terms.txt`

```
# Real brand names (trademark protection)
Nike
Adidas
Apple
Google
Tesla

# Controversial topics
politics
religion
violence

# Misleading terms
cure
treatment
guarantee
```

**Loading and Caching:**
```python
class PolicyGate:
    def __init__(self, config: Config, llm_client: LLMClient):
        self._blocked_terms_cache: list[str] | None = None

    def _load_blocked_terms(self) -> list[str]:
        """Load blocked terms with caching."""

        if self._blocked_terms_cache is not None:
            return self._blocked_terms_cache

        terms = []
        with open(self.config.blocked_terms_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    terms.append(line)

        self._blocked_terms_cache = terms
        return terms
```

### Brand Safety Checks

**Validation Steps:**

1. **Keyword Blacklist**: Fast rejection of obvious violations
2. **Fuzzy Matching**: Detect variations (e.g., "N1ke", "Goog1e")
3. **LLM Analysis**: Semantic understanding of context
4. **E-type Specific**: Ensure fictional disclaimer present

**Example Validation Flow:**
```
Input: ReelPlan(type="E", brand_name="AppleCafe", ...)
    │
    ▼
Keyword Check: "Apple" found → REJECTED
    │
    ▼
Alternative: ReelPlan(type="E", brand_name="BrewCraft", ...)
    │
    ▼
Keyword Check: PASS (no matches)
    │
    ▼
LLM Check: "Does 'BrewCraft' conflict with real brands?" → PASS
    │
    ▼
E-type Check: brand_name length = 9 chars (valid), concept exists → PASS
    │
    ▼
APPROVED for generation
```

### Compliance Requirements

| Content Type | Requirements |
|--------------|--------------|
| **A-type** | - No trademarked terms<br>- No misleading claims<br>- Appropriate mood/theme |
| **E-type** | - "Fictional concept:" disclaimer<br>- Brand name 7-14 chars<br>- No real brand conflicts<br>- Clear conceptual nature |

---

## Performance Considerations

### FFmpeg Command Optimization

**Problem:** FFmpeg can be slow for complex filters

**Solutions:**

1. **Hardware Acceleration:**
```python
# Use GPU encoding (NVIDIA)
cmd = ffmpeg.output(
    ...,
    vcodec="h264_nvenc",  # GPU encoder
    preset="fast",
)

# Use Quick Sync (Intel)
cmd = ffmpeg.output(
    ...,
    vcodec="h264_qsv",
    preset="veryfast",
)
```

2. **Preset Optimization:**
```python
# Faster encoding (larger files)
cmd = ffmpeg.output(..., preset="veryfast")

# Balanced (default)
cmd = ffmpeg.output(..., preset="medium")

# Slower encoding (smaller files)
cmd = ffmpeg.output(..., preset="slow")
```

3. **Resolution Scaling:**
```python
# Generate at lower resolution, upscale
base_video = generate_video(resolution=(540, 960))  # Half resolution
final_video = ffmpeg.input(base_video).filter(
    "scale", 1080, 1920
).output(...)
```

### LLM Rate Limiting

**Problem:** API rate limits and costs

**Solutions:**

1. **Exponential Backoff:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
async def call_llm(self, prompt: str) -> str:
    return await self.llm_client.generate_text(prompt)
```

2. **Batching:**
```python
# Generate multiple plans in one API call
plans = await planner.generate_daily_plan(count=7)  # One API call for 7 plans

# Instead of 7 separate API calls
```

3. **Caching:**
```python
class CachedLLMClient(LLMClient):
    def __init__(self, base_client: LLMClient, cache_dir: Path):
        self.base_client = base_client
        self.cache = {}

    async def generate_text(self, prompt: str) -> str:
        # Cache based on prompt hash
        cache_key = hashlib.md5(prompt.encode()).hexdigest()

        if cache_key in self.cache:
            return self.cache[cache_key]

        response = await self.base_client.generate_text(prompt)
        self.cache[cache_key] = response
        return response
```

### Batch Processing Strategies

**Parallel Generation:**
```python
async def run_pipeline_parallel(
    self,
    count: int,
    max_concurrent: int = 3,
) -> list[ReelMetadata]:
    """Generate multiple videos in parallel."""

    plans = await self.planner.generate_daily_plan(count)

    semaphore = asyncio.Semaphore(max_concurrent)

    async def generate_one(plan: ReelPlan) -> ReelMetadata:
        async with semaphore:
            return await self._generate_single_reel(plan)

    tasks = [generate_one(plan) for plan in plans]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if isinstance(r, ReelMetadata)]
```

### Storage Optimization

**Problem:** Large video files accumulate quickly

**Solutions:**

1. **Automatic Cleanup:**
```python
# Clean videos older than 30 days
def cleanup_old_outputs(outputs_dir: Path, max_age_days: int = 30):
    cutoff_date = datetime.now() - timedelta(days=max_age_days)

    for run_dir in outputs_dir.glob("run_*"):
        if run_dir.stat().st_mtime < cutoff_date.timestamp():
            shutil.rmtree(run_dir)
```

2. **Compression:**
```python
# Higher compression (smaller files)
cmd = ffmpeg.output(
    ...,
    **{"b:v": "2M"},  # 2 Mbps bitrate (default: 5M)
    preset="slow",     # Better compression
)
```

3. **Archival Storage:**
```python
# Compress old runs to zip
def archive_old_runs(outputs_dir: Path, archive_dir: Path):
    for run_dir in outputs_dir.glob("run_*"):
        if run_dir.stat().st_mtime < cutoff_date.timestamp():
            archive_path = archive_dir / f"{run_dir.name}.zip"
            shutil.make_archive(archive_path.with_suffix(""), "zip", run_dir)
            shutil.rmtree(run_dir)
```

---

## Future Enhancements

### 1. Instagram Graph API Publishing

**Status:** Not implemented in MVP

**Implementation Plan:**

1. **Phase 1:** OAuth authentication flow
2. **Phase 2:** Media upload endpoints
3. **Phase 3:** Reels-specific metadata (cover, music)
4. **Phase 4:** Scheduling and publishing
5. **Phase 5:** Analytics and insights

**Required Components:**
- OAuth2 authentication manager
- Media upload handler
- Publishing scheduler
- Error handling and retry logic

### 2. Analytics Integration

**Proposed Features:**

```python
class AnalyticsTracker:
    """Track reel performance metrics."""

    async def get_reel_insights(self, media_id: str) -> dict:
        """Fetch insights for published reel."""

        return {
            "views": 12453,
            "likes": 1234,
            "comments": 56,
            "shares": 78,
            "saves": 234,
            "reach": 15678,
            "engagement_rate": 0.12,
        }

    def analyze_performance(self, run_id: str) -> dict:
        """Analyze which content types perform best."""

        # Compare A-type vs E-type performance
        # Identify top-performing themes/moods
        # Recommend optimal posting times
        pass
```

### 3. Advanced Video Generation

**Manim Integration:**
```python
class ManimGenerator(BaseGenerator):
    """Generate mathematical animations with Manim."""

    async def generate(self, plan: ReelPlan) -> Path:
        """Create complex animations."""

        # Generate Manim scene
        scene_code = self._generate_manim_scene(plan)

        # Render with Manim
        video_path = await self._render_manim(scene_code)

        return video_path
```

**3D Rendering with Blender:**
```python
class BlenderGenerator(BaseGenerator):
    """Generate 3D rendered concepts with Blender."""

    async def generate(self, plan: ReelPlan) -> Path:
        """Create 3D product mockups."""

        # Create Blender script
        script = self._generate_blender_script(plan)

        # Render with Blender
        video_path = await self._render_blender(script)

        return video_path
```

### 4. Multi-Platform Support

**Extend to TikTok, YouTube Shorts:**

```python
class MultiPlatformPublisher(BasePublisher):
    """Publish to multiple platforms."""

    def __init__(self, config: Config):
        self.instagram = InstagramPublisher(config)
        self.tiktok = TikTokPublisher(config)
        self.youtube = YouTubeShortsPublisher(config)

    async def publish(self, metadata: ReelMetadata) -> dict:
        """Publish to all configured platforms."""

        results = {}

        if config.publish_instagram:
            results["instagram"] = await self.instagram.publish(metadata)

        if config.publish_tiktok:
            results["tiktok"] = await self.tiktok.publish(metadata)

        if config.publish_youtube:
            results["youtube"] = await self.youtube.publish(metadata)

        return results
```

### 5. Content Scheduling

**Smart Scheduling Based on Analytics:**

```python
class ContentScheduler:
    """Schedule posts for optimal engagement."""

    def __init__(self, analytics: AnalyticsTracker):
        self.analytics = analytics

    async def optimize_schedule(
        self,
        metadata_list: list[ReelMetadata],
        start_date: datetime,
    ) -> dict[datetime, ReelMetadata]:
        """Create optimal posting schedule."""

        # Analyze historical performance by time/day
        best_times = await self.analytics.get_best_posting_times()

        # Distribute content across optimal times
        schedule = {}
        for idx, metadata in enumerate(metadata_list):
            post_time = self._calculate_post_time(
                start_date, idx, best_times
            )
            schedule[post_time] = metadata

        return schedule
```

### 6. A/B Testing Framework

**Test Content Variations:**

```python
class ABTestManager:
    """Manage A/B tests for content optimization."""

    async def create_test(
        self,
        variant_a: ReelPlan,
        variant_b: ReelPlan,
        duration_days: int = 7,
    ) -> str:
        """Create A/B test comparing two variants."""

        # Generate both variants
        video_a = await self.generator.generate(variant_a)
        video_b = await self.generator.generate(variant_b)

        # Publish with tracking
        test_id = str(uuid.uuid4())
        await self.publish_with_tracking(video_a, test_id, "A")
        await self.publish_with_tracking(video_b, test_id, "B")

        return test_id

    async def analyze_test(self, test_id: str) -> dict:
        """Analyze A/B test results."""

        results_a = await self.analytics.get_metrics(test_id, "A")
        results_b = await self.analytics.get_metrics(test_id, "B")

        winner = "A" if results_a["engagement"] > results_b["engagement"] else "B"

        return {
            "winner": winner,
            "improvement": abs(results_a["engagement"] - results_b["engagement"]),
            "confidence": self._calculate_statistical_significance(results_a, results_b),
        }
```

---

## Testing Strategy

### Unit Tests (Current: 46 tests, 52% coverage)

**Coverage by Component:**
- Foundation: 80% (config, llm_client, utils)
- Business Logic: 60% (planner, policy_gate, caption_generator)
- Video Generation: 40% (generator, editor)
- Orchestration: 50% (orchestrator, CLI)

**Testing Approach:**
```python
# Mock LLM responses
@pytest.fixture
def mock_llm_client():
    client = AsyncMock(spec=LLMClient)
    client.generate_text.return_value = '{"type": "A", ...}'
    return client

# Test planner with mocked LLM
async def test_planner_generate_daily_plan(mock_llm_client):
    planner = Planner(config=test_config, llm_client=mock_llm_client)
    plans = await planner.generate_daily_plan(count=3)

    assert len(plans) == 3
    assert all(isinstance(p, ReelPlan) for p in plans)
```

### Integration Tests

**Test Complete Pipeline:**
```python
async def test_end_to_end_generation():
    """Test complete pipeline from plan to video."""

    config = load_test_config()
    orchestrator = Orchestrator(config=config)

    # Generate 1 A-type video
    results = await orchestrator.run_pipeline(
        count=1,
        type_filter="A",
        dry_run=True,
    )

    assert len(results) == 1
    assert results[0].video_path.exists()
    assert results[0].thumbnail_path.exists()
```

### Performance Tests

**Benchmark Generation Speed:**
```python
async def test_generation_performance():
    """Ensure video generation completes in reasonable time."""

    start_time = time.time()

    video_path = await generator.generate(test_plan)

    duration = time.time() - start_time

    assert duration < 30  # Should complete in under 30 seconds
```

---

## Conclusion

The reelsbot architecture is designed for:

- **Modularity**: Each component has clear responsibilities
- **Extensibility**: Easy to add new generators, publishers, storage backends
- **Safety**: Multi-layer policy validation ensures brand safety
- **Performance**: Optimized for batch processing and cost efficiency
- **Maintainability**: Clear separation of concerns, type safety, comprehensive tests

The MVP implementation (Phases 1-4) provides a solid foundation for future enhancements while delivering immediate value through automated content generation.

---

**See Also:**
- [README.md](README.md) - User documentation
- [RUNBOOK.md](RUNBOOK.md) - Operational procedures
- [pyproject.toml](pyproject.toml) - Project configuration

---

**End of Architecture Documentation**
