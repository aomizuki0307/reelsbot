# Reelsbot Architecture

## System Overview

The reelsbot system is built in phases, with Phase 1 (Foundation) providing the core infrastructure for all subsequent components.

## Phase 1: Foundation Layer (COMPLETE)

```
┌─────────────────────────────────────────────────────────────────┐
│                         FOUNDATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐     │
│  │ Configuration  │  │   Logging    │  │  Path Utilities │     │
│  │   (Pydantic)   │  │  (Run-ID)    │  │   (FFmpeg)      │     │
│  └────────────────┘  └──────────────┘  └─────────────────┘     │
│                                                                  │
│  ┌────────────────┐  ┌──────────────────────────────────────┐  │
│  │  Brand Name    │  │       LLM Client Abstraction         │  │
│  │   Generator    │  │   (Anthropic Claude / OpenAI GPT)    │  │
│  └────────────────┘  └──────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Dependencies

```
Application Layer (Future Phases)
        │
        ├─── Phase 2: Content Generator
        │         │
        │         ├─── Abstract Generator ──┐
        │         ├─── Educational Generator │
        │         └─── Policy Validator      │
        │                                     │
        ├─── Phase 3: Video Editor           │
        │         │                           │
        │         ├─── Text Renderer          │
        │         ├─── Video Compositor       │
        │         └─── Audio Manager          │
        │                                     │
        └─── Phase 4: Publisher              │
                  │                           │
                  └─── Meta Graph API        │
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                           │
│                                                                  │
│  ReelsbotConfig ◄─── .env file                                  │
│       │                                                          │
│       ├─── setup_logger(run_id) ──► Logger with Run-ID tracking│
│       │                                                          │
│       ├─── LLMClient ──► Anthropic / OpenAI APIs               │
│       │                                                          │
│       ├─── BrandNameGenerator ──► Fictional Brand Names         │
│       │                                                          │
│       └─── Path Utilities ──► Windows-safe path handling        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Typical Execution Flow

```
1. Initialize
   ├── Load config from .env
   ├── Setup logger with run_id
   └── Create output directory

2. Generate Content
   ├── Generate brand name
   ├── Call LLM for concept/fact
   ├── Validate against policies
   └── Retry if needed

3. Create Video (Phase 3)
   ├── Render text frames
   ├── Compose video with ffmpeg
   └── Save to output directory

4. Publish (Phase 4)
   └── Upload to Instagram via Meta API
```

### Configuration Flow

```
.env file
   │
   ▼
pydantic-settings
   │
   ├─── Validation
   │       ├── API key presence
   │       ├── Duration ranges
   │       └── A/E ratio sum
   │
   ▼
ReelsbotConfig object
   │
   ├──► LLMClient (API keys, model selection)
   ├──► Logger (log directories)
   ├──► Path utilities (output directories)
   └──► Generator (duration settings, ratios)
```

### Logging Flow

```
Application Event
   │
   ▼
logger.info/warning/error()
   │
   ├──► File Handler ──► logs/YYYYMMDD.log (UTF-8)
   │                      Format: [run_id] LEVEL: message
   │
   └──► Console Handler ──► stdout
                            Format: [run_id] LEVEL: message
```

### LLM Client Flow

```
Application Request
   │
   ▼
LLMClient.generate(system, user, temp, tokens)
   │
   ├── Provider Selection (config.llm_provider)
   │   │
   │   ├── "anthropic" ──► Anthropic client
   │   │                    │
   │   │                    └─── messages.create()
   │   │
   │   └── "openai" ──► OpenAI client
   │                     │
   │                     └─── chat.completions.create()
   │
   ├── Retry Logic (tenacity)
   │   └── Max 3 attempts with exponential backoff
   │
   └── Response ──► Generated text
```

## File Organization

```
reelsbot/
│
├── src/reelsbot/                   # Source code
│   ├── __init__.py                 # Package exports
│   ├── config.py                   # Configuration (Pydantic)
│   ├── llm_client.py               # LLM abstraction
│   │
│   ├── utils/                      # Utility modules
│   │   ├── __init__.py
│   │   ├── logger.py               # Logging setup
│   │   ├── paths.py                # Path utilities
│   │   └── brand_name.py           # Brand generator
│   │
│   ├── generator/                  # Phase 2 (Future)
│   ├── editor/                     # Phase 3 (Future)
│   ├── publisher/                  # Phase 4 (Future)
│   └── storage/                    # Phase 5 (Future)
│
├── tests/                          # Unit tests
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_paths.py
│   ├── test_brand_name.py
│   └── test_llm_client.py
│
├── examples/                       # Usage examples
│   └── foundation_usage.py
│
├── docs/                           # Documentation
│   ├── PHASE1_FOUNDATION.md
│   └── ARCHITECTURE.md (this file)
│
├── policies/                       # Safety policies
│   └── blocked_terms.txt
│
├── prompts/                        # LLM prompts
│   └── (Phase 2)
│
├── outputs/                        # Generated content
│   └── {run_id}/
│
├── logs/                           # Log files
│   └── YYYYMMDD.log
│
├── pyproject.toml                  # Dependencies
├── .env.example                    # Environment template
├── .env                            # Environment (gitignored)
└── test_foundation.py              # Quick validation
```

## Component Interactions

### Configuration Component

```
ReelsbotConfig
│
├── Providers
│   ├── llm_provider: "anthropic" | "openai"
│   ├── anthropic_api_key
│   ├── anthropic_model
│   ├── openai_api_key
│   └── openai_model
│
├── Video Settings
│   ├── duration ranges (A: 8-12s, E: 10-14s)
│   ├── resolution (1080x1920)
│   ├── aspect_ratio (9:16)
│   └── fps (30)
│
├── Safety
│   ├── policy_max_retry (3)
│   └── blocked_terms_path
│
├── Ratios
│   ├── default_a_ratio (70%)
│   └── default_e_ratio (30%)
│
└── Paths
    ├── outputs_dir
    ├── logs_dir
    └── ffmpeg_path
```

### Logger Component

```
setup_logger(run_id) ──┐
                       │
    ┌──────────────────┴─────────────────┐
    │                                     │
    ▼                                     ▼
FileHandler                         ConsoleHandler
    │                                     │
    ├── File: logs/YYYYMMDD.log          ├── Stream: stdout
    ├── Encoding: UTF-8                  ├── Level: configurable
    ├── Format: Detailed with timestamp  └── Format: Concise
    └── Level: configurable
```

### Path Utilities Component

```
Path Utilities
│
├── to_ffmpeg_path(path)
│   └── C:\path\file.mp4 ──► C:/path/file.mp4
│
├── ensure_output_dir(run_id, base_dir)
│   └── Creates: base_dir/run_id/
│
├── safe_filename(name)
│   └── Removes: < > : " / \ | ? *
│
└── get_temp_path(base_dir, run_id, suffix)
    └── Returns: base_dir/run_id/temp{suffix}
```

### Brand Name Generator Component

```
BrandNameGenerator
│
├── Components
│   ├── Common Nouns (12): Wave, Peak, Echo, ...
│   └── Syllables (15): vo, ri, ka, ne, ...
│
├── Generation
│   ├── Format: Noun + 2-3 syllables
│   ├── Length: 7-14 characters
│   └── Seed support for reproducibility
│
├── Validation
│   ├── is_safe(brand)
│   ├── Check: length, alpha-only
│   └── Reject: forbidden fragments
│
└── Output Examples
    ├── WaveVoria
    ├── PeakMalune
    └── EchoTivra
```

### LLM Client Component

```
LLMClient
│
├── Initialization
│   ├── config: ReelsbotConfig
│   ├── logger: Logger
│   └── provider-specific client
│
├── Methods
│   ├── generate(system, user, temp, tokens)
│   │   ├── Async operation
│   │   ├── Retry with exponential backoff
│   │   └── Returns: str
│   │
│   └── get_model_info()
│       └── Returns: {provider, model}
│
└── Providers
    ├── Anthropic
    │   ├── messages.create()
    │   └── Models: claude-sonnet-4-*
    │
    └── OpenAI
        ├── chat.completions.create()
        └── Models: gpt-4-*
```

## Design Patterns

### 1. Dependency Injection
```python
# Configuration injected into components
client = LLMClient(config, logger)
```

### 2. Factory Pattern
```python
# Factory function for client creation
client = await create_llm_client(config)
```

### 3. Strategy Pattern
```python
# Different providers with same interface
if provider == "anthropic":
    use_anthropic_client()
elif provider == "openai":
    use_openai_client()
```

### 4. Retry Pattern
```python
# Automatic retry with exponential backoff
@retry(stop=stop_after_attempt(3))
async def generate(...):
    ...
```

## Error Handling Strategy

```
Application Error
   │
   ├── Configuration Error
   │   ├── Missing API key ──► ValueError with clear message
   │   ├── Invalid ratio ──► ValueError (must sum to 100)
   │   └── Invalid duration ──► ValidationError
   │
   ├── LLM Error
   │   ├── API Error ──► Retry up to 3 times
   │   ├── Empty response ──► LLMError
   │   └── Network error ──► LLMError after retries
   │
   ├── Path Error
   │   ├── Invalid characters ──► Sanitized automatically
   │   └── Missing directory ──► Created automatically
   │
   └── Logging Error
       └── Setup before use ──► RuntimeError if not initialized
```

## Security & Safety

```
Safety Measures
│
├── Configuration
│   ├── API keys from environment (not hardcoded)
│   └── .env file in .gitignore
│
├── Brand Names
│   ├── Forbidden fragments list
│   └── Validation before use
│
├── File Operations
│   ├── Safe filename generation
│   └── Directory creation with exist_ok
│
└── LLM Calls
    ├── Retry limits (max 3 attempts)
    └── Error logging for debugging
```

## Performance Considerations

```
Performance Optimizations
│
├── Async LLM Calls
│   └── Non-blocking API requests
│
├── Path Caching
│   └── pathlib.Path for efficient operations
│
├── Logger Setup
│   └── Single initialization per run
│
└── Brand Generation
    └── Seed support for reproducibility
```

## Testing Strategy

```
Testing Approach
│
├── Unit Tests (60+ tests)
│   ├── Configuration validation
│   ├── Brand name generation
│   ├── Path utilities
│   ├── Logger setup
│   └── LLM client (mocked)
│
├── Integration Tests
│   └── test_foundation.py
│
├── Example Scripts
│   └── examples/foundation_usage.py
│
└── Coverage
    └── ~95% code coverage
```

---

**Architecture Document Version**: 1.0
**Last Updated**: 2025-12-19
**Phase**: 1 (Foundation) - COMPLETE
