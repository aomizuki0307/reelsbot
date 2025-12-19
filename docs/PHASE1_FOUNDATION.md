# Phase 1: Foundation Layer - Implementation Documentation

## Overview

This document describes the Phase 1 foundation layer implementation for the reelsbot Instagram Reels automation system. This layer provides the core infrastructure that all other components depend on.

## Implemented Modules

### 1. Configuration Management (`src/reelsbot/config.py`)

Type-safe configuration management using Pydantic Settings.

**Key Features:**
- Environment variable loading from `.env` files
- Type validation with Pydantic
- Sensible defaults for all settings
- Validation of configuration integrity (API keys, ratios, duration ranges)

**Main Classes:**
- `ReelsbotConfig`: Main configuration class with all settings
- `load_config()`: Convenience function to load and validate configuration

**Configuration Categories:**
- LLM Settings: Provider selection, API keys, models, generation parameters
- Video Settings: Duration ranges, resolution, aspect ratio, FPS
- Safety Settings: Max retries, blocked terms path
- A/E Mix Ratio: Percentage split between abstract and educational content
- Path Settings: Output directories, log directories
- FFmpeg Settings: Path to ffmpeg executable

**Example Usage:**
```python
from reelsbot import load_config

config = load_config()
print(f"Using {config.llm_provider} with model {config.get_active_model()}")
print(f"Video resolution: {config.video_resolution}")
```

### 2. Logging (`src/reelsbot/utils/logger.py`)

Structured logging with run-ID tracking for execution flow monitoring.

**Key Features:**
- Run-ID included in all log messages
- Dual output: date-based log files and console
- UTF-8 encoding for international character support (Japanese, emoji)
- Configurable log levels for file and console independently

**Main Functions:**
- `setup_logger(run_id, logs_dir, level, console_level)`: Initialize logger
- `get_logger()`: Get the configured logger instance
- `update_run_id(run_id)`: Update run ID for subsequent messages

**Example Usage:**
```python
from reelsbot.utils import setup_logger

logger = setup_logger("run_20250101_123456")
logger.info("Processing started")
logger.warning("Resource usage high")
logger.error("Failed to process video")
```

**Log Format:**
```
2025-01-01 12:34:56 [run_20250101_123456] INFO: Processing started
2025-01-01 12:34:57 [run_20250101_123456] WARNING: Resource usage high
```

### 3. Path Utilities (`src/reelsbot/utils/paths.py`)

Windows-safe path handling with ffmpeg compatibility.

**Key Features:**
- Convert Windows paths to ffmpeg-compatible format (forward slashes)
- Create and manage output directories per run
- Safe filename generation (removes invalid characters)
- Temporary file path generation

**Main Functions:**
- `to_ffmpeg_path(path)`: Convert Windows path to ffmpeg format
- `ensure_output_dir(run_id, base_dir)`: Create and return run output directory
- `ensure_dir(path)`: Ensure directory exists
- `safe_filename(filename, max_length)`: Generate safe filename
- `get_temp_path(base_dir, run_id, suffix)`: Generate temporary file path

**Example Usage:**
```python
from pathlib import Path
from reelsbot.utils import to_ffmpeg_path, ensure_output_dir, safe_filename

# Convert Windows path for ffmpeg
windows_path = Path("C:\\Users\\name\\video.mp4")
ffmpeg_path = to_ffmpeg_path(windows_path)  # "C:/Users/name/video.mp4"

# Create output directory
output_dir = ensure_output_dir("run_123")  # outputs/run_123/

# Generate safe filename
safe_name = safe_filename("My Video: Part 1?")  # "My Video Part 1"
```

### 4. Brand Name Generator (`src/reelsbot/utils/brand_name.py`)

Generate fictional brand names for content that avoids real brand similarities.

**Key Features:**
- Format: CommonNoun + 2-3 syllable coined word
- Length: 7-14 characters
- English letters only (no numbers/symbols)
- Excludes real brand fragments
- Reproducible with seed support

**Main Classes:**
- `BrandNameGenerator`: Main generator class
- `generate_brand_name(seed)`: Convenience function

**Example Usage:**
```python
from reelsbot.utils import BrandNameGenerator, generate_brand_name

# Simple generation
brand = generate_brand_name()  # "WaveVoria"

# Batch generation with reproducibility
generator = BrandNameGenerator(seed=42)
brands = generator.generate_batch(10)
# ['MistVonu', 'BloomTanu', 'AuraNeka', ...]

# Validation
generator.is_safe("WaveVoria")  # True
generator.is_safe("AppleCore")  # False (contains 'apple')
```

**Brand Format:**
- Prefixes: Wave, Peak, Echo, Flux, Aura, Pulse, Drift, Spark, Glow, Haze, Mist, Bloom
- Syllables: vo, ri, ka, ne, lu, ma, ti, so, ra, vi, ta, nu, ko, fe, la
- Examples: WaveVoria, PeakMalune, EchoTivra, FluxKane

### 5. LLM Client Abstraction (`src/reelsbot/llm_client.py`)

Unified interface for Anthropic Claude and OpenAI GPT models.

**Key Features:**
- Single API for both Anthropic and OpenAI
- Automatic provider selection from configuration
- Retry logic with exponential backoff (using tenacity)
- Type-safe async interface
- Error handling with informative messages

**Main Classes:**
- `LLMClient`: Main client class
- `LLMError`: Exception for LLM-related errors
- `create_llm_client(config, logger)`: Factory function

**Example Usage:**
```python
from reelsbot import load_config, create_llm_client

config = load_config()
client = await create_llm_client(config)

response = await client.generate(
    system_prompt="You are a creative assistant.",
    user_prompt="Generate a concept for an abstract video.",
    temperature=0.8,
    max_tokens=500
)

print(response)
```

**Supported Providers:**
- Anthropic: Claude models (claude-sonnet-4-20250514, etc.)
- OpenAI: GPT models (gpt-4-turbo-preview, etc.)

**Retry Behavior:**
- Maximum 3 attempts
- Exponential backoff: 2s, 4s, 8s (with jitter)
- Retries on API errors only

## Installation

The package uses `pyproject.toml` with modern Python packaging:

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

## Testing

Comprehensive test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/reelsbot --cov-report=term-missing

# Run specific test module
pytest tests/test_config.py
pytest tests/test_brand_name.py
pytest tests/test_paths.py
pytest tests/test_logger.py
pytest tests/test_llm_client.py
```

**Test Coverage:**
- Configuration validation and loading
- Brand name generation and safety checks
- Path utilities and Windows compatibility
- Logger setup and run-ID tracking
- LLM client initialization and mocking

## Type Checking

The codebase uses complete type hints for all functions:

```bash
# Run mypy type checker
mypy src/reelsbot
```

## Code Quality

The project follows Python best practices:

```bash
# Format code with black
black src/reelsbot tests

# Lint with ruff
ruff check src/reelsbot tests

# Fix auto-fixable issues
ruff check --fix src/reelsbot tests
```

## Quick Test Script

A simple test script is provided to verify the implementation without requiring API keys:

```bash
python test_foundation.py
```

This script tests:
- All imports
- Brand name generation
- Path utilities
- Logger setup
- Configuration loading
- LLM client initialization (without API calls)

## Environment Setup

Create a `.env` file based on `.env.example`:

```bash
# LLM Provider
LLM_PROVIDER=anthropic

# Anthropic Settings
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Video Settings
DEFAULT_A_DURATION_MIN=8
DEFAULT_A_DURATION_MAX=12
DEFAULT_E_DURATION_MIN=10
DEFAULT_E_DURATION_MAX=14

# A/E Mix Ratio
DEFAULT_A_RATIO=70
DEFAULT_E_RATIO=30

# Paths
OUTPUTS_DIR=outputs
LOGS_DIR=logs
BLOCKED_TERMS_PATH=policies/blocked_terms.txt

# FFmpeg
FFMPEG_PATH=ffmpeg
```

## Next Steps

With the foundation layer complete, the following components can now be built:

1. **Content Generator** (Phase 2)
   - Abstract concept generation
   - Educational fact generation
   - Policy validation
   - Brand name integration

2. **Video Editor** (Phase 3)
   - Text rendering with Pillow
   - Video composition with ffmpeg
   - Transition effects
   - Audio integration

3. **Publisher** (Phase 4)
   - Meta Graph API integration
   - Instagram Reels upload
   - Metadata management

## Design Decisions

### Why Pydantic Settings?
- Type-safe configuration with validation
- Automatic environment variable loading
- Easy to test with dependency injection
- Clear error messages for misconfiguration

### Why Standard Logging?
- Well-understood Python standard library
- Easy to integrate with existing tools
- UTF-8 support for international content
- Flexible handler configuration

### Why Async LLM Client?
- Prepares for concurrent operations
- Non-blocking API calls
- Better resource utilization
- Standard pattern for API clients

### Why pathlib?
- Modern, object-oriented path handling
- Cross-platform compatibility
- Better than string manipulation
- Type-safe with mypy

## Dependencies

Core dependencies from `pyproject.toml`:

```toml
dependencies = [
    "anthropic>=0.18.1,<1.0.0",
    "openai>=1.0.0,<2.0.0",
    "pydantic>=2.0.0,<3.0.0",
    "pydantic-settings>=2.0.0,<3.0.0",
    "python-dotenv>=1.0.0,<2.0.0",
    "tenacity>=8.2.0,<9.0.0",
]
```

## API Reference

See inline docstrings for complete API documentation. All public functions and classes have comprehensive docstrings with:
- Purpose description
- Parameter descriptions with types
- Return value description
- Usage examples
- Exception documentation

## Contributing

When extending the foundation layer:

1. Maintain complete type hints
2. Add comprehensive docstrings
3. Write tests for new functionality
4. Ensure Windows compatibility
5. Update this documentation

## License

See LICENSE file in project root.
