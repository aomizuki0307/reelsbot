# reelsbot

> Instagram Reels automation pipeline with AI-powered abstract and fictional content generation

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-46%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-52%25-yellow.svg)](htmlcov/)

## Overview

**reelsbot** is a fully automated Instagram Reels content generation system that creates two types of engaging video content:

- **A-type (Abstract)**: Mesmerizing visual loops with inspirational taglines (8-12 seconds)
- **E-type (Educational/Fictional)**: Fictional brand concepts and designs (10-14 seconds)

The system handles the entire pipeline: content planning, video generation, caption writing, policy validation, and publishing (dry-run mode in MVP).

### Key Features

- LLM-powered content planning (Anthropic Claude or OpenAI GPT)
- Automated video generation with FFmpeg
- Smart caption generation with hashtags
- Dual-layer policy compliance system
- Customizable A/E content mix ratio
- Comprehensive logging and metadata tracking
- Windows-first development with cross-platform support

---

## Quick Start

Get up and running in under 10 minutes:

```powershell
# 1. Clone or navigate to the project
cd C:\path\to\reelsbot

# 2. Install uv (Python package manager)
pip install uv

# 3. Setup environment and dependencies
make setup

# 4. Configure API keys in .env
notepad .env  # Add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# 5. Run demo (generates 1 A + 1 E video)
make run-demo
```

Check `outputs/` directory for generated videos!

---

## Installation

### Prerequisites

Before installing reelsbot, ensure you have:

1. **Python 3.10 or higher**
   ```powershell
   python --version  # Should show 3.10.x or higher
   ```
   Download from: https://www.python.org/downloads/

2. **FFmpeg** (required for video generation)

   **Windows Installation:**
   ```powershell
   # Using Chocolatey (recommended)
   choco install ffmpeg

   # Or using Scoop
   scoop install ffmpeg

   # Or download manually from https://ffmpeg.org/download.html
   # Extract to C:\ffmpeg and add C:\ffmpeg\bin to PATH
   ```

   **Verify installation:**
   ```powershell
   ffmpeg -version
   ```

3. **uv** (Python package manager - faster than pip)
   ```powershell
   pip install uv
   ```

### Installation Steps

#### Option 1: Using Makefile (Recommended)

```powershell
# Setup everything automatically
make setup

# This will:
# - Create virtual environment (.venv)
# - Install all dependencies
# - Create required directories (outputs/, logs/)
# - Copy .env.example to .env
```

#### Option 2: Manual Installation

```powershell
# 1. Create virtual environment
uv venv .venv

# 2. Activate virtual environment
.venv\Scripts\activate  # PowerShell
# OR
.venv\Scripts\activate.bat  # CMD

# 3. Install reelsbot with dependencies
uv pip install -e ".[dev]"

# 4. Create directories
mkdir outputs, logs, policies

# 5. Copy environment file
copy .env.example .env
```

### Environment Configuration

Edit `.env` and configure your settings:

```ini
# Required: Choose LLM provider
LLM_PROVIDER=anthropic  # or "openai"

# Required: Add your API key
ANTHROPIC_API_KEY=sk-ant-api03-...  # Get from https://console.anthropic.com/
# OR
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com/

# Optional: Customize settings
DEFAULT_A_RATIO=70  # 70% Abstract content
DEFAULT_E_RATIO=30  # 30% Educational content
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `anthropic` | LLM provider: `anthropic` or `openai` |
| `ANTHROPIC_API_KEY` | Conditional* | - | Anthropic API key |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-20250514` | Anthropic model name |
| `OPENAI_API_KEY` | Conditional* | - | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4-turbo-preview` | OpenAI model name |
| `DEFAULT_A_DURATION_MIN` | No | `8` | Min seconds for A-type videos |
| `DEFAULT_A_DURATION_MAX` | No | `12` | Max seconds for A-type videos |
| `DEFAULT_E_DURATION_MIN` | No | `10` | Min seconds for E-type videos |
| `DEFAULT_E_DURATION_MAX` | No | `14` | Max seconds for E-type videos |
| `DEFAULT_A_RATIO` | No | `70` | Percentage of A-type content |
| `DEFAULT_E_RATIO` | No | `30` | Percentage of E-type content |
| `POLICY_MAX_RETRY` | No | `3` | Max retries for policy validation |
| `OUTPUTS_DIR` | No | `outputs` | Output directory for videos |
| `LOGS_DIR` | No | `logs` | Log directory |
| `FFMPEG_PATH` | No | `ffmpeg` | Path to FFmpeg executable |

\* *Either ANTHROPIC_API_KEY or OPENAI_API_KEY is required, depending on LLM_PROVIDER*

### API Key Setup

#### Anthropic (Recommended)

1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-api03-...`

#### OpenAI (Alternative)

1. Visit https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Add to `.env`: `OPENAI_API_KEY=sk-...`

---

## Usage

### CLI Commands Overview

reelsbot provides 4 main commands:

```powershell
python -m reelsbot plan       # Generate content plan
python -m reelsbot run        # Generate videos
python -m reelsbot validate   # Validate metadata
python -m reelsbot info       # Show configuration
```

### 1. Planning (`plan`)

Generate a content plan without creating videos:

```powershell
# Generate 7-day plan with default 70:30 ratio
python -m reelsbot plan --count 7

# Custom ratio (60% A, 40% E)
python -m reelsbot plan --count 5 --ratio 60:40

# Save plan to file
python -m reelsbot plan --count 7 --output plan.json

# Plan for specific date
python -m reelsbot plan --date 2025-12-25 --count 7
```

**Output Example:**
```
Generated Content Plan:

  1. [A] Gradient - Find peace in motion
     Duration: 10s, Mood: calm

  2. [E] BrewCraft - Modern Cafe Interior
     Duration: 12s, Mood: minimal

  3. [A] Kinetic - Embrace the rhythm
     Duration: 9s, Mood: energetic

Summary: 5 Abstract, 2 Educational
```

### 2. Generation (`run`)

Generate and save videos:

```powershell
# Generate 1 abstract video (dry-run mode)
python -m reelsbot run --count 1 --type A

# Generate 1 educational video
python -m reelsbot run --count 1 --type E

# Generate 7 videos with mixed ratio (70:30)
python -m reelsbot run --count 7 --mix

# Live mode (requires Instagram credentials - not implemented in MVP)
python -m reelsbot run --count 1 --type A --live
```

**Options:**
- `--count N`: Number of videos to generate (default: 1)
- `--type A|E`: Generate specific type (mutually exclusive with --mix)
- `--mix`: Use A/E ratio from config (mutually exclusive with --type)
- `--dry-run` (default): Save locally only
- `--live`: Publish to Instagram (requires API credentials)

**Output:**
```
Complete! 2 video(s) generated.

Video 1:
  Type: A
  Title: Gradient - Find peace in motion
  Video: C:\...\outputs\run_20251219_143022\video_1.mp4
  Thumbnail: C:\...\outputs\run_20251219_143022\thumbnail_1.png
  Caption: Let your mind drift with the flow...

Video 2:
  Type: E
  Title: BrewCraft - Modern Cafe Interior
  Video: C:\...\outputs\run_20251219_143022\video_2.mp4
  Thumbnail: C:\...\outputs\run_20251219_143022\thumbnail_2.png
  Caption: Fictional concept: BrewCraft, a modern cafe...

Output directory: C:\...\outputs\run_20251219_143022
```

### 3. Validation (`validate`)

Re-validate generated content against current policies:

```powershell
# Validate a single metadata file
python -m reelsbot validate outputs\run_20251219_143022\metadata_1.json

# Validate all metadata in a directory (PowerShell)
Get-ChildItem outputs\run_*\metadata_*.json | ForEach-Object {
    python -m reelsbot validate $_.FullName
}
```

### 4. Info (`info`)

Display current configuration and system status:

```powershell
python -m reelsbot info
```

**Output:**
```
Configuration:
  Version: 0.1.0
  LLM Provider: anthropic
  Model: claude-sonnet-4-20250514
  Video Resolution: 1080x1920
  FPS: 30
  A/E Ratio: 70:30

Duration Ranges:
  Abstract (A): 8-12s
  Educational (E): 10-14s

Paths:
  Outputs: C:\...\outputs
  Logs: C:\...\logs
  FFmpeg: ffmpeg
```

---

## Content Types Explained

### A-type: Abstract Visual Loops

**Purpose:** Calming, mesmerizing visual content with inspirational taglines

**Characteristics:**
- Duration: 8-12 seconds
- Seamlessly looping animations
- Minimal text overlay (tagline)
- Themes: gradient, geometric, kinetic, particles
- Moods: calm, dreamy, energetic, minimal, hypnotic

**Example:**
- Theme: `gradient`
- Tagline: "Find peace in motion"
- Mood: `calm`
- Video: Smooth gradient transitions with floating particles

### E-type: Educational/Fictional Concepts

**Purpose:** Showcase fictional brand designs and concepts

**Characteristics:**
- Duration: 10-14 seconds
- Fictional brand name (7-14 characters)
- Must include "Fictional concept" in caption
- Categories: cafe, packaging, poster, app_ui, product_design, place_concept
- Moods: minimal, modern, vibrant, elegant

**Example:**
- Brand Name: `BrewCraft`
- Concept: "Modern Cafe Interior"
- Category: `cafe`
- Video: 3D rendered cafe interior with branding

---

## Output Structure

Each generation run creates a timestamped directory:

```
outputs/
└── run_20251219_143022/
    ├── video_1.mp4          # Generated video file (1080x1920, 30fps)
    ├── thumbnail_1.png      # Video thumbnail (1080x1920)
    ├── metadata_1.json      # Complete metadata
    ├── video_2.mp4
    ├── thumbnail_2.png
    └── metadata_2.json
```

### Metadata JSON Format

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
  "caption": "Let your mind drift with the flow of endless gradients...",
  "hashtags": ["abstractart", "visualart", "calmvibes"],
  "video_path": "outputs/run_20251219_143022/video_1.mp4",
  "thumbnail_path": "outputs/run_20251219_143022/thumbnail_1.png",
  "status": "generated"
}
```

### Video Specifications

- **Resolution:** 1080x1920 (9:16 vertical, Instagram Reels optimized)
- **Frame Rate:** 30 fps
- **Codec:** H.264 (libx264)
- **Audio:** Optional background music (not in MVP)
- **Format:** MP4

---

## Troubleshooting

### FFmpeg Not Found

**Error:**
```
[ERROR] ffmpeg not found in PATH
```

**Solution:**
```powershell
# Check if FFmpeg is installed
ffmpeg -version

# If not installed, install via Chocolatey
choco install ffmpeg

# Or add FFmpeg to PATH manually
setx PATH "%PATH%;C:\ffmpeg\bin"

# Restart terminal and verify
ffmpeg -version
```

### API Key Errors

**Error:**
```
[ERROR] API key not configured
```

**Solution:**
1. Check `.env` file exists
2. Verify API key is set: `ANTHROPIC_API_KEY=sk-ant-...`
3. Ensure no extra spaces around the `=` sign
4. Restart terminal after editing `.env`

### LLM Timeout Issues

**Error:**
```
[ERROR] LLM request timed out
```

**Solution:**
- Check internet connection
- Verify API key is valid and has credits
- Try reducing `--count` to generate fewer videos
- Check LLM provider status page:
  - Anthropic: https://status.anthropic.com/
  - OpenAI: https://status.openai.com/

### Path Issues on Windows

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**Solution:**
- Use absolute paths or run from project root
- Avoid spaces in directory names
- Use forward slashes `/` or escaped backslashes `\\` in paths
- Run `make setup` to ensure directories exist

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'reelsbot'
```

**Solution:**
```powershell
# Ensure package is installed in editable mode
uv pip install -e ".[dev]"

# Activate virtual environment if not active
.venv\Scripts\activate
```

### Virtual Environment Issues

**Error:**
```
[ERROR] Virtual environment not found
```

**Solution:**
```powershell
# Recreate virtual environment
make setup

# Or manually
uv venv .venv
.venv\Scripts\activate
uv pip install -e ".[dev]"
```

---

## Development

### Running Tests

```powershell
# Run all tests with coverage
make test

# Run specific test file
python -m pytest tests/test_planner.py

# Run with verbose output
python -m pytest -v

# View coverage report in browser
start htmlcov\index.html
```

### Code Quality

```powershell
# Run linting checks (ruff + mypy)
make lint

# Format code (black + ruff)
make format

# Check specific file
python -m ruff check src/reelsbot/planner.py
python -m mypy src/reelsbot/planner.py
```

### Project Structure

```
reelsbot/
├── src/
│   └── reelsbot/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── cli.py               # CLI interface
│       ├── config.py            # Configuration
│       ├── models.py            # Data models
│       ├── llm_client.py        # LLM abstraction
│       ├── planner.py           # Content planning
│       ├── policy_gate.py       # Policy validation
│       ├── caption_generator.py # Caption generation
│       ├── orchestrator.py      # Pipeline orchestration
│       ├── generator/           # Video generation
│       │   ├── base.py
│       │   └── ffmpeg_dummy.py
│       ├── editor/              # Video editing
│       │   └── ffmpeg_editor.py
│       ├── publisher/           # Publishing
│       │   ├── base.py
│       │   └── dry_run.py
│       ├── storage/             # Data storage
│       │   └── runs.py
│       └── utils/               # Utilities
│           ├── logger.py
│           ├── paths.py
│           ├── ffmpeg.py
│           ├── image.py
│           └── brand_name.py
├── tests/                       # Test suite (46 tests)
├── policies/                    # Policy configurations
│   └── blocked_terms.txt
├── outputs/                     # Generated videos
├── logs/                        # Application logs
├── pyproject.toml               # Project metadata
├── .env.example                 # Environment template
├── Makefile                     # Build automation
└── README.md                    # This file
```

### Contributing Guidelines

1. **Fork & Clone**
   ```powershell
   git clone https://github.com/yourusername/reelsbot.git
   ```

2. **Create Feature Branch**
   ```powershell
   git checkout -b feature/amazing-feature
   ```

3. **Make Changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Run Quality Checks**
   ```powershell
   make format  # Format code
   make lint    # Check code quality
   make test    # Run tests
   ```

5. **Commit & Push**
   ```powershell
   git add .
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

6. **Open Pull Request**
   - Describe changes clearly
   - Reference related issues
   - Ensure CI passes

---

## Common Workflows

### Daily Production Run

```powershell
# 1. Generate plan for the week
python -m reelsbot plan --count 7 --output weekly_plan.json

# 2. Generate videos for today (2 videos)
python -m reelsbot run --count 2 --mix --dry-run

# 3. Review output in outputs/ directory

# 4. Publish to Instagram (when live mode is ready)
# python -m reelsbot run --count 2 --mix --live
```

### Testing New Content Ideas

```powershell
# Test abstract concept
python -m reelsbot run --count 1 --type A --dry-run

# Test educational concept
python -m reelsbot run --count 1 --type E --dry-run

# Validate against policy
python -m reelsbot validate outputs\run_*\metadata_1.json
```

### Batch Generation

```powershell
# Generate 30 videos (1 month of content)
python -m reelsbot run --count 30 --mix --dry-run

# Check outputs
dir outputs\run_*\*.mp4
```

---

## Roadmap

### Phase 1: Foundation (COMPLETED)
- Configuration management
- LLM client abstraction
- Logging and utilities

### Phase 2: Business Logic (COMPLETED)
- Content planning
- Policy gate
- Caption generation
- Storage management

### Phase 3: Video Generation (COMPLETED)
- FFmpeg-based video generator
- Video editor with overlays
- Image utilities

### Phase 4: Orchestration (COMPLETED)
- Pipeline orchestrator
- CLI interface
- Dry-run publisher

### Phase 5: Instagram Publishing & Scheduling (COMPLETED)
- Instagram Graph API integration
- S3-compatible and static URL storage adapters
- Scheduled posting with SQLite queue
- Background worker daemon
- Rate limiting and retry logic
- Token masking for security

---

## Instagram Publishing

reelsbot now supports automated publishing to Instagram via the Graph API, with both immediate and scheduled posting capabilities.

### Setup Requirements

1. **Instagram Professional Account** (Business or Creator)
   - Convert your account at: Instagram Settings → Account → Switch to Professional Account

2. **Facebook Developer App**
   - Create app at: https://developers.facebook.com/apps/
   - Add Instagram Basic Display product
   - Configure permissions: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`

3. **Long-Lived Access Token**
   - Generate at: https://developers.facebook.com/tools/explorer/
   - Exchange for 60-day token (see Meta documentation)
   - Get Instagram User ID from: `https://graph.facebook.com/v22.0/me/accounts?access_token=YOUR_TOKEN`

4. **Storage Configuration**

   **Option A: S3-Compatible Storage (Recommended)**
   ```ini
   STORAGE_TYPE=s3
   STORAGE_S3_BUCKET=your-bucket-name
   STORAGE_S3_ACCESS_KEY=your-access-key
   STORAGE_S3_SECRET_KEY=your-secret-key
   STORAGE_S3_REGION=us-east-1
   ```

   **Option B: Static File Serving**
   ```ini
   STORAGE_TYPE=static
   STORAGE_STATIC_BASE_URL=https://cdn.example.com/reels/
   ```

5. **Configure `.env`**
   ```ini
   IG_USER_ID=your-instagram-user-id
   IG_ACCESS_TOKEN=your-long-lived-access-token
   ```

### Usage

#### Immediate Publishing

Publish a previously generated run immediately:

```powershell
# Generate videos first
python -m reelsbot run --count 1 --type A --dry-run

# Publish immediately to Instagram
python -m reelsbot publish run_20251220_123456 --now

# Publish and share to main feed
python -m reelsbot publish run_20251220_123456 --now --share-to-feed
```

#### Scheduled Publishing

Generate videos and schedule for later:

```powershell
# Schedule for Christmas Day at 6PM UTC
python -m reelsbot enqueue --count 3 --mix --schedule-at 2025-12-25T18:00:00Z

# Schedule for tomorrow at noon
python -m reelsbot enqueue --count 1 --type A --schedule-at 2025-12-21T12:00:00Z
```

**Start the worker** to process scheduled posts:

```powershell
# Run worker with default 45s interval
python -m reelsbot worker

# Custom interval
python -m reelsbot worker --interval 60

# Background daemon (Windows: use pythonw.exe)
pythonw -m reelsbot worker --daemon
```

### Storage Adapters

#### S3-Compatible (AWS, MinIO, DigitalOcean Spaces)

Generates presigned URLs valid for 1 hour (default):

```ini
STORAGE_TYPE=s3
STORAGE_S3_BUCKET=reelsbot-videos
STORAGE_S3_ENDPOINT=https://s3.amazonaws.com
STORAGE_S3_PRESIGNED_EXPIRY=3600
```

**Benefits:**
- Private storage with temporary public URLs
- Works with AWS S3, MinIO, DigitalOcean Spaces, etc.
- Automatic URL expiration for security

#### Static URL (nginx, CDN)

Copies files to local directory for static serving:

```ini
STORAGE_TYPE=static
STORAGE_STATIC_BASE_URL=https://cdn.example.com/reels/
STORAGE_STATIC_OUTPUT_DIR=outputs/static
```

**Benefits:**
- Simple setup with nginx or any web server
- No cloud storage costs
- Suitable for small-scale deployments

### Rate Limits & Safety

Instagram enforces the following limits:

- **50 posts per 24 hours** (media_publish endpoint)
- **100 posts per 24 hours** (overall)
- **400 container creations per 24 hours**

reelsbot automatically:
- Tracks publish count and warns when approaching limit
- Retries on transient errors (5xx, network timeouts)
- Fails safely on policy violations (UNSAFE_CONTENT, EXPIRED containers)
- Masks access tokens in logs (shows only last 4 characters)

### Troubleshooting Instagram Publishing

#### Container Expired Error

**Error:**
```
ContainerExpiredError: Container expired. Containers expire after 24 hours.
```

**Solution:**
- Containers have 24-hour validity
- Re-enqueue with fresh schedule time
- Worker will automatically recreate container

#### Rate Limit Exceeded

**Error:**
```
RateLimitError: Rate limit reached: 50/50 posts in 24h
```

**Solution:**
- Wait for rate limit window to reset (24 hours)
- Reduce posting frequency
- Check `IG_RATE_LIMIT_PER_DAY` setting

#### Unsafe Content

**Error:**
```
UnsafeContentError: Content flagged as unsafe
```

**Solution:**
- Review generated content
- Regenerate with different parameters
- Check caption complies with Instagram policies

#### Invalid Video Format

**Error:**
```
InvalidVideoError: Video format or duration invalid
```

**Solution:**
- Ensure video is MP4, H.264 codec
- Duration must be 3-90 seconds for Reels
- Resolution should be 1080x1920 (9:16)

#### Token Issues

**Error:**
```
ValueError: Instagram configuration incomplete
```

**Solution:**
```powershell
# Verify .env settings
notepad .env

# Check token is valid
# IG_USER_ID=123456789
# IG_ACCESS_TOKEN=your-token-here

# Test configuration
python -m reelsbot info
```

### Monitoring Scheduled Posts

Check scheduled posts in SQLite:

```powershell
# View all scheduled posts
sqlite3 outputs\db\reelsbot.db "SELECT * FROM scheduled_posts WHERE status='QUEUED';"

# View failed posts
sqlite3 outputs\db\reelsbot.db "SELECT * FROM scheduled_posts WHERE status='FAILED';"

# View recently published
sqlite3 outputs\db\reelsbot.db "SELECT * FROM scheduled_posts WHERE status='PUBLISHED' ORDER BY published_at DESC LIMIT 10;"
```

---

## Privacy Policy & Terms of Service

Our privacy policy and terms of service for Instagram Graph API usage:
- **Privacy Policy**: https://aomizuki0307.github.io/reelsbot/privacy.html
- **Terms of Service**: https://aomizuki0307.github.io/reelsbot/terms.html

### Data Deletion Requests

If you wish to delete your data from our application:
1. Send an email to **groob66610@gmail.com** with the subject "Data Deletion Request"
2. Include your Instagram User ID
3. We will process your request within 30 days

For more information, see our [Privacy Policy](https://aomizuki0307.github.io/reelsbot/privacy.html).

---

### Future Enhancements
- Advanced video generation (Manim, 3D rendering)
- Analytics dashboard
- Multi-platform support (TikTok, YouTube Shorts)
- Custom music library integration
- A/B testing framework

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Support

- **Issues:** https://github.com/yourusername/reelsbot/issues
- **Documentation:** See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- **Operations:** See [RUNBOOK.md](RUNBOOK.md) for production deployment

---

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/) and [OpenAI GPT](https://openai.com/)
- Video processing powered by [FFmpeg](https://ffmpeg.org/)
- Package management by [uv](https://github.com/astral-sh/uv)

---

Made with automation in mind.
