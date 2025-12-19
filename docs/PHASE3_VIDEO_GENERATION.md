# Phase 3: Video Generation & Editing

Complete implementation of FFmpeg-based video generation and editing for the reelsbot Instagram Reels automation system.

## Overview

Phase 3 implements the video generation and editing layer, providing:

- **Generator Base Interface**: Abstract class defining the video generation contract
- **FFmpeg Dummy Generator**: Pure FFmpeg-based video generation (no external APIs)
- **FFmpeg Editor**: Video post-processing with overlays and thumbnails
- **Utility Modules**: FFmpeg and image processing helpers

## Architecture

```
src/reelsbot/
├── generator/
│   ├── __init__.py
│   ├── base.py              # BaseGenerator abstract class
│   └── ffmpeg_dummy.py      # FFmpegDummyGenerator implementation
├── editor/
│   ├── __init__.py
│   └── ffmpeg_editor.py     # FFmpegEditor for post-processing
└── utils/
    ├── ffmpeg.py            # FFmpeg command helpers
    └── image.py             # PIL image generation
```

## Components

### 1. Generator Base Interface (`generator/base.py`)

Abstract base class defining the video generation contract:

```python
from reelsbot.generator import BaseGenerator

class BaseGenerator(ABC):
    @abstractmethod
    def generate_A_video(plan: ReelPlan, output_path: Path) -> Path:
        """Generate abstract loop video for A-type content."""

    @abstractmethod
    def generate_E_video(plan: ReelPlan, output_path: Path) -> Path:
        """Generate fictional concept video for E-type content."""

    def generate(plan: ReelPlan, output_dir: Path) -> Path:
        """Unified entry point (routes to A or E based on plan type)."""
```

**Key Features**:
- Unified `generate()` method with automatic routing
- Type validation for A/E plans
- Consistent return types (Path to generated video)

### 2. FFmpeg Dummy Generator (`generator/ffmpeg_dummy.py`)

Pure FFmpeg-based video generator (no external APIs):

```python
from reelsbot.generator import FFmpegDummyGenerator

generator = FFmpegDummyGenerator(config, logger)
video_path = generator.generate(plan, output_dir)
```

**A-Type Video Generation**:
- **Gradient Theme**: Dynamic color gradients using `lavfi` + `geq` filter
- **Geometric Theme**: Rotating patterns using `testsrc2` + `rotate`
- **Kinetic Theme**: Animated moving boxes using `drawbox`
- **Particles Theme**: Particle-like effect using `nullsrc` + `geq` + noise

**E-Type Video Generation**:
1. Create background image with PIL (brand name, concept, category shape)
2. Apply camera motion with FFmpeg `zoompan` filter (slow zoom from 1.0 to 1.3)

**Video Specifications**:
- Resolution: 1080x1920 (9:16 aspect ratio)
- Frame rate: 30fps
- Codec: H.264 (libx264), yuv420p pixel format
- Audio: None (silent)
- Duration: plan.duration_sec (8-12s for A, 10-14s for E)

### 3. FFmpeg Editor (`editor/ffmpeg_editor.py`)

Video post-processing with overlays and thumbnails:

```python
from reelsbot.editor import FFmpegEditor

editor = FFmpegEditor(config, logger)
final_video, thumbnail = editor.compose(raw_video, plan, output_dir)
```

**Features**:
- **A-Type Composition**: Add tagline text overlay (bottom-center, white with black shadow)
- **E-Type Composition**: Add "Fictional concept" overlay (CRITICAL REQUIREMENT)
  - Black background box (450x90px, 60% opacity)
  - White text "Fictional concept" (Arial Bold, 36px)
  - Position: top-left (30, 30)
  - Displayed from 0.5s to end
- **Thumbnail Generation**: Extract frame at 1 second as JPG

**Critical E-Type Overlay**:

The "Fictional concept" overlay is a MANDATORY requirement for E-type videos to clearly mark them as containing fictional/educational content. This overlay is visible in the video file itself (not just metadata).

### 4. FFmpeg Utilities (`utils/ffmpeg.py`)

Helper functions for FFmpeg command execution:

```python
from reelsbot.utils.ffmpeg import (
    check_ffmpeg_available,
    run_ffmpeg_command,
    build_filter_complex,
    get_video_info,
    convert_to_h264,
)

# Check FFmpeg availability
if not check_ffmpeg_available():
    raise RuntimeError("FFmpeg not found")

# Execute FFmpeg command
cmd = ["ffmpeg", "-i", "input.mp4", "-vf", "scale=1920:1080", "output.mp4"]
run_ffmpeg_command(cmd, logger)

# Build complex filter string
filters = ["scale=1920:1080", "drawtext=..."]
filter_str = build_filter_complex(filters)
```

**Key Features**:
- FFmpeg availability check with timeout
- Command execution with logging and error handling
- Windows path compatibility (uses `to_ffmpeg_path()`)
- Video info extraction with ffprobe
- H.264 conversion utility

### 5. Image Utilities (`utils/image.py`)

PIL-based image generation for E-type backgrounds:

```python
from reelsbot.utils.image import (
    create_concept_background,
    add_text_to_image,
    CATEGORY_COLORS,
)

# Create background for E-type video
bg_path = create_concept_background(plan, temp_dir)

# Add text to image
img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))
add_text_to_image(img, "Hello", (540, 960), 48, (0, 0, 0), align="center")
```

**Category Colors**:
- cafe: Warm beige (245, 240, 235)
- packaging: Cool white (250, 250, 255)
- poster: Light blue (240, 245, 250)
- app_ui: Neutral gray (248, 248, 252)
- product_design: Cream (252, 248, 243)
- place_concept: Light steel blue (238, 242, 245)

**Background Elements**:
- Category-specific background color
- Brand name (center, Arial Bold 84px)
- Concept title (Arial 42px)
- Minimal geometric shape (category icon)

## Usage Examples

### Complete Pipeline (A-Type)

```python
from reelsbot import load_config
from reelsbot.generator import FFmpegDummyGenerator
from reelsbot.editor import FFmpegEditor
from reelsbot.models import ReelPlan
from reelsbot.utils import setup_logger

# Setup
config = load_config()
logger = setup_logger("video_gen")
generator = FFmpegDummyGenerator(config, logger)
editor = FFmpegEditor(config, logger)

# Create A-type plan
plan = ReelPlan(
    type="A",
    theme="gradient",
    mood="calm",
    duration_sec=10,
    tagline="A moment of peace"
)

# Generate raw video
raw_video = generator.generate(plan, Path("output"))

# Add overlay and create thumbnail
final_video, thumbnail = editor.compose(raw_video, plan, Path("output"))

print(f"Final video: {final_video}")
print(f"Thumbnail: {thumbnail}")
```

### Complete Pipeline (E-Type)

```python
# Create E-type plan
plan = ReelPlan(
    type="E",
    theme="cafe",
    mood="calm",
    duration_sec=12,
    brand_name="ZENITHCAFE",
    concept_title="Modern Cafe Interior",
    category="cafe"
)

# Generate raw video (creates background image + camera motion)
raw_video = generator.generate(plan, Path("output"))

# Add "Fictional concept" overlay and create thumbnail
final_video, thumbnail = editor.compose(raw_video, plan, Path("output"))

# The final video now includes the "Fictional concept" overlay
print(f"Final video with overlay: {final_video}")
```

### All Themes Demo

```python
themes = ["gradient", "geometric", "kinetic", "particles"]

for theme in themes:
    plan = ReelPlan(
        type="A",
        theme=theme,
        mood="calm",
        duration_sec=8,
        tagline=f"{theme.title()} patterns"
    )

    raw_video = generator.generate(plan, Path("output"))
    final_video, thumbnail = editor.compose(raw_video, plan, Path("output"))
```

## FFmpeg Requirements

### Installation

**Windows**:
```powershell
# Using winget
winget install ffmpeg

# Or download from https://ffmpeg.org/download.html
# Add to PATH: C:\ffmpeg\bin
```

**Linux**:
```bash
sudo apt-get install ffmpeg
```

**macOS**:
```bash
brew install ffmpeg
```

### Verification

```python
from reelsbot.utils.ffmpeg import check_ffmpeg_available

if check_ffmpeg_available():
    print("FFmpeg is ready!")
else:
    print("FFmpeg not found in PATH")
```

## Windows Compatibility

All FFmpeg operations are Windows-compatible:

1. **Path Handling**: Uses `to_ffmpeg_path()` to convert Windows paths to FFmpeg format
2. **Font Paths**: Uses `C:/Windows/Fonts/arial.ttf` (forward slashes)
3. **Command Execution**: Handles Windows subprocess quirks
4. **Error Handling**: Proper stderr capture on Windows

## Testing

### Run All Tests

```bash
pytest tests/test_phase3_integration.py -v
pytest tests/test_utils_ffmpeg.py -v
pytest tests/test_utils_image.py -v
```

### Run Demo Script

```bash
python examples/demo_video_generation.py
```

The demo script generates:
- A-type abstract video with tagline overlay
- E-type fictional concept video with "Fictional concept" overlay
- All theme variations

### Test Coverage

The test suite includes:
- **Unit Tests**: FFmpeg utilities, image utilities
- **Integration Tests**: Generator + Editor pipeline
- **Mock Tests**: FFmpeg commands (no actual FFmpeg execution required)
- **E-Type Overlay Verification**: Ensures "Fictional concept" overlay is added

## Error Handling

### FFmpeg Not Available

```python
from reelsbot.utils.ffmpeg import check_ffmpeg_available

if not check_ffmpeg_available():
    raise RuntimeError(
        "FFmpeg is not available. Please install FFmpeg and add it to PATH. "
        "Download from: https://ffmpeg.org/download.html"
    )
```

### Command Execution Errors

All FFmpeg commands include:
- Availability check before execution
- Timeout protection (default: 300s)
- Detailed error logging with stderr output
- Automatic retry logic (future enhancement)

### Image Generation Errors

- Validates plan type (A vs E)
- Validates required fields (brand_name, concept_title, category)
- Fallback to default colors for unknown categories
- Graceful font fallback (Arial → DejaVu → default)

## Performance Considerations

### Video Generation Times

Approximate generation times (depends on hardware):
- **A-Type (gradient)**: ~5-10 seconds for 10s video
- **A-Type (geometric)**: ~8-15 seconds for 10s video
- **A-Type (kinetic)**: ~5-10 seconds for 10s video
- **A-Type (particles)**: ~10-20 seconds for 10s video
- **E-Type (concept)**: ~3-8 seconds for 12s video
- **Overlay composition**: ~2-5 seconds
- **Thumbnail extraction**: <1 second

### Optimization Tips

1. **Use shorter durations during development** (8s instead of 12s)
2. **Adjust FFmpeg preset** for faster encoding (use "fast" or "ultrafast")
3. **Batch process** multiple videos in parallel
4. **Cache intermediate results** (raw videos before overlay)

## Critical Requirements Checklist

- ✅ **E-Type Overlay**: "Fictional concept" label visible in video
- ✅ **Resolution**: All videos 1080x1920 (9:16)
- ✅ **Silent**: No audio track
- ✅ **Windows Compatible**: All paths work on Windows
- ✅ **Loop Quality**: A-type videos should loop seamlessly
- ✅ **Theme Variety**: 4 different A-type themes
- ✅ **Category Support**: 6+ E-type categories with unique backgrounds

## Next Steps (Phase 4)

Phase 3 is complete! Next phases:

1. **Phase 4: Orchestration** - Main workflow combining all components
2. **Phase 5: Scheduling** - Automated daily posting
3. **Phase 6: Analytics** - Track engagement and optimize content

## Troubleshooting

### FFmpeg Not Found

```
RuntimeError: FFmpeg is not available
```

**Solution**: Install FFmpeg and add to PATH (see FFmpeg Requirements above)

### Font Not Found (Linux)

```
Error: Cannot load font 'C:/Windows/Fonts/arial.ttf'
```

**Solution**: Fonts automatically fall back to DejaVu on Linux. No action needed.

### Video Generation Timeout

```
subprocess.TimeoutExpired: Command 'ffmpeg...' timed out after 300 seconds
```

**Solution**: Increase timeout in `run_ffmpeg_command(cmd, logger, timeout=600)`

### PIL Image Errors

```
OSError: cannot identify image file
```

**Solution**: Ensure Pillow is installed: `pip install Pillow`

## API Reference

See inline documentation in:
- `src/reelsbot/generator/base.py`
- `src/reelsbot/generator/ffmpeg_dummy.py`
- `src/reelsbot/editor/ffmpeg_editor.py`
- `src/reelsbot/utils/ffmpeg.py`
- `src/reelsbot/utils/image.py`

All functions include comprehensive docstrings with examples.
