# Reelsbot Quick Start Guide

**Version**: 0.1.0
**Last Updated**: 2025-12-19

## Installation

### 1. Prerequisites

- Python 3.11 or higher
- FFmpeg installed and in PATH
- Anthropic or OpenAI API key

### 2. Install Reelsbot

```bash
cd reelsbot
pip install -e .
```

### 3. Configure Environment

Copy `.env.example` to `.env` and set your API key:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Required: Set your API key
ANTHROPIC_API_KEY=your-actual-api-key-here

# Or use OpenAI instead
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-openai-api-key-here
```

### 4. Verify Installation

```bash
python -m reelsbot info
```

---

## Basic Usage

### Generate Your First Video

**Abstract (A-type) Video**:
```bash
python -m reelsbot run --count 1 --type A --dry-run
```

**Educational (E-type) Video**:
```bash
python -m reelsbot run --count 1 --type E --dry-run
```

**Output Location**:
```
outputs/run_YYYYMMDD_HHMMSS/
├── video_1.mp4
├── thumbnail_1.jpg
└── metadata_1.json
```

---

## Common Commands

### Generate Daily Plan

```bash
# Default 7 posts with 70:30 A:E ratio
python -m reelsbot plan --count 7

# Custom ratio
python -m reelsbot plan --count 5 --ratio 60:40

# Save to file
python -m reelsbot plan --count 7 --output my_plan.json
```

### Generate Multiple Videos

```bash
# 7 videos with mixed A/E ratio
python -m reelsbot run --count 7 --mix --dry-run
```

### Validate Metadata

```bash
python -m reelsbot validate outputs/run_20251220_123456/metadata_1.json
```

### Check Configuration

```bash
python -m reelsbot info
```

---

## Understanding Content Types

### A-Type: Abstract Loops
- **Visual**: Gradient, geometric, kinetic, particles
- **Duration**: 8-12 seconds
- **Overlay**: Short tagline (3-7 words)
- **Purpose**: Aesthetic, mood-based content

**Example**:
```json
{
  "type": "A",
  "theme": "gradient",
  "mood": "calm",
  "duration_sec": 10,
  "tagline": "A moment of peace"
}
```

### E-Type: Educational/Fictional
- **Visual**: Fictional brand concepts
- **Duration**: 10-14 seconds
- **Overlay**: "Fictional concept" disclaimer
- **Purpose**: Design education, inspiration

**Example**:
```json
{
  "type": "E",
  "theme": "cafe",
  "mood": "calm",
  "duration_sec": 12,
  "brand_name": "ZENITH",
  "concept_title": "Modern Cafe Interior",
  "category": "cafe"
}
```

---

## Output Structure

### Video Files

```
outputs/run_YYYYMMDD_HHMMSS/
├── video_1.mp4              # Final video with overlays
├── thumbnail_1.jpg          # Auto-generated thumbnail
├── metadata_1.json          # Complete metadata
└── raw_video_1.mp4          # (Optional) Raw video before editing
```

### Metadata Format

```json
{
  "run_id": "run_20251220_123456",
  "timestamp": "2025-12-20T12:34:56",
  "plan": {
    "type": "A",
    "theme": "gradient",
    "mood": "calm",
    "duration_sec": 10,
    "tagline": "A moment of peace"
  },
  "caption": "Embrace the calm of abstract gradients...",
  "hashtags": ["abstractart", "calmaesthetic", "visualart"],
  "video_path": "outputs/run_20251220_123456/video_1.mp4",
  "thumbnail_path": "outputs/run_20251220_123456/thumbnail_1.jpg",
  "status": "generated"
}
```

---

## Configuration Options

### Environment Variables (.env)

```bash
# LLM Provider (required)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here

# Video Settings
DEFAULT_A_DURATION_MIN=8
DEFAULT_A_DURATION_MAX=12
DEFAULT_E_DURATION_MIN=10
DEFAULT_E_DURATION_MAX=14

# A/E Mix Ratio
DEFAULT_A_RATIO=70
DEFAULT_E_RATIO=30

# Safety
POLICY_MAX_RETRY=3

# Paths
OUTPUTS_DIR=outputs
LOGS_DIR=logs
FFMPEG_PATH=ffmpeg
```

---

## Troubleshooting

### FFmpeg Not Found

**Error**: `FFmpeg not found in PATH`

**Solution**:
1. Install FFmpeg: https://ffmpeg.org/download.html
2. Add to PATH, or set in `.env`:
   ```bash
   FFMPEG_PATH=C:\path\to\ffmpeg.exe
   ```

### Invalid API Key

**Error**: `Invalid authentication token`

**Solution**:
1. Check your API key in `.env`
2. Verify it's not expired
3. Ensure no extra spaces or quotes

### Policy Validation Failed

**Error**: `Policy validation failed after 3 attempts`

**Solution**:
1. Check logs for specific violations
2. Review blocked terms in `policies/blocked_terms.txt`
3. Adjust prompts if needed

### Unicode Encoding Error

**Error**: `UnicodeEncodeError: 'cp932' codec can't encode...`

**Solution**:
- This is already fixed in the latest version
- Upgrade to version 0.1.0 or later

---

## Workflow Examples

### Example 1: Daily Content Creation

```bash
# 1. Plan your week
python -m reelsbot plan --count 7 --output weekly_plan.json

# 2. Generate all content
python -m reelsbot run --count 7 --mix --dry-run

# 3. Review outputs in outputs/run_YYYYMMDD_HHMMSS/

# 4. (Future) Publish to Instagram
python -m reelsbot run --count 7 --mix --live
```

### Example 2: Test Different Types

```bash
# Test A-type
python -m reelsbot run --count 1 --type A --dry-run

# Test E-type
python -m reelsbot run --count 1 --type E --dry-run

# Compare results
ls -la outputs/
```

### Example 3: Validate Old Content

```bash
# After updating policies, re-validate existing content
for file in outputs/run_*/metadata_*.json; do
    python -m reelsbot validate "$file"
done
```

---

## Best Practices

### 1. Always Test with DRY_RUN First

```bash
# Good: Test first
python -m reelsbot run --count 1 --type A --dry-run

# Then: Go live
python -m reelsbot run --count 1 --type A --live
```

### 2. Use Plans for Consistency

```bash
# Generate plan first
python -m reelsbot plan --count 7 --output plan.json

# Review plan, then execute
python -m reelsbot run --count 7 --mix --dry-run
```

### 3. Monitor Logs

```bash
# Check logs for issues
tail -f logs/YYYYMMDD.log
```

### 4. Organize Outputs

```bash
# Rename run directories for tracking
mv outputs/run_20251220_123456 outputs/week_2025_12_20
```

### 5. Backup Metadata

```bash
# Save metadata for tracking
cp outputs/run_*/metadata_*.json backups/
```

---

## Performance Tips

### 1. Batch Generation

Generate multiple videos in one run for efficiency:

```bash
# Better: Generate all at once
python -m reelsbot run --count 7 --mix --dry-run

# Slower: Generate one by one
for i in {1..7}; do
    python -m reelsbot run --count 1 --type A --dry-run
done
```

### 2. Parallel Processing (Future)

Currently sequential, but future versions will support:
- Parallel video generation
- Async LLM calls
- Concurrent uploads

### 3. Reuse Plans

```bash
# Generate plan once
python -m reelsbot plan --count 7 --output plan.json

# Use same plan multiple times (for testing)
# (Feature to be added: --plan-file option)
```

---

## Safety Features

### 1. Policy Gate

All content automatically validated against:
- Blocked terms list
- Type-specific requirements
- Overlay requirements

### 2. Retry Logic

If policy validation fails:
1. Automatically regenerates plan
2. Retries up to 3 times
3. Logs all violations

### 3. DRY_RUN Mode

Default mode for safety:
- No external API calls
- Local file storage only
- Perfect for testing

### 4. Content Logging

All operations logged with:
- Run ID tracking
- Timestamp
- Full error details

---

## CLI Reference

### Global Options

```bash
--version          Show version and exit
--help             Show help message
```

### Commands

```bash
plan               Generate daily posting plan
run                Generate and publish reels
validate           Re-validate metadata
info               Show system information
```

### Command Options

**plan**:
```bash
--date TEXT        Plan date (YYYY-MM-DD)
--count INTEGER    Number of posts [default: 7]
--ratio TEXT       A:E ratio [default: 70:30]
--output PATH      Save to JSON file
```

**run**:
```bash
--count INTEGER    Number of videos [default: 1]
--type [A|E]       Video type (mutually exclusive with --mix)
--mix              Use A/E ratio from config
--dry-run/--live   Mode [default: dry-run]
```

**validate**:
```bash
METADATA_PATH      Path to metadata JSON file
```

---

## Getting Help

### Command Help

```bash
# Global help
python -m reelsbot --help

# Command-specific help
python -m reelsbot run --help
python -m reelsbot plan --help
python -m reelsbot validate --help
```

### Check Logs

```bash
# View today's log
cat logs/$(date +%Y%m%d).log

# Follow live log
tail -f logs/$(date +%Y%m%d).log
```

### Verify Configuration

```bash
python -m reelsbot info
```

---

## Next Steps

1. **Generate Test Content**
   ```bash
   python -m reelsbot run --count 1 --type A --dry-run
   ```

2. **Review Outputs**
   ```bash
   ls -la outputs/run_*/
   ```

3. **Check Video Quality**
   - Open video in media player
   - Verify overlays are correct
   - Check thumbnail quality

4. **Adjust Configuration**
   - Modify `.env` settings
   - Update blocked terms if needed
   - Customize prompts

5. **Scale Up**
   ```bash
   python -m reelsbot run --count 7 --mix --dry-run
   ```

6. **Go Live** (when ready)
   ```bash
   python -m reelsbot run --count 1 --type A --live
   ```

---

## FAQ

**Q: How long does it take to generate a video?**
A: 10-15 seconds for A-type, 12-18 seconds for E-type (depends on LLM API latency).

**Q: Can I customize the video themes?**
A: Yes, modify the prompts in `prompts/` directory.

**Q: How do I change the A/E ratio?**
A: Set `DEFAULT_A_RATIO` and `DEFAULT_E_RATIO` in `.env` (must sum to 100).

**Q: What if FFmpeg is not in PATH?**
A: Set `FFMPEG_PATH` in `.env` to the full path to ffmpeg executable.

**Q: Can I use OpenAI instead of Anthropic?**
A: Yes, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY` in `.env`.

**Q: How do I schedule automatic posting?**
A: Use cron (Linux/Mac) or Task Scheduler (Windows) with `--live` flag. (Future: built-in scheduler)

**Q: Where are the logs stored?**
A: In `logs/YYYYMMDD.log` (one file per day).

**Q: How do I validate old content?**
A: Use `python -m reelsbot validate path/to/metadata.json`

**Q: Can I edit the generated videos?**
A: Yes, videos are standard MP4 files. Edit with any video editor.

**Q: How do I update policies?**
A: Edit `policies/blocked_terms.txt` and re-run validation.

---

**Happy Content Creating!** 🎬
