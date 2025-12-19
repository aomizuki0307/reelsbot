# Phase 2 Quick Reference Guide

## Import Cheatsheet

```python
# Main imports
from reelsbot import (
    # Models
    ReelPlan,
    ReelMetadata,

    # Core modules
    Planner,
    PolicyGate,
    CaptionGenerator,
    RunStorage,
    DryRunPublisher,

    # Configuration
    load_config,
    create_llm_client,
)

# Utilities
from reelsbot.utils import setup_logger
```

---

## Common Patterns

### 1. Initialize System

```python
import asyncio
from reelsbot import load_config, create_llm_client
from reelsbot.utils import setup_logger

async def init():
    config = load_config()
    logger = setup_logger("my_script")
    llm_client = await create_llm_client(config, logger)
    return config, logger, llm_client

config, logger, llm_client = asyncio.run(init())
```

### 2. Create a Plan

```python
from reelsbot import Planner

planner = Planner(config, llm_client, logger)

# Daily plan
plans = await planner.generate_daily_plan("2025-12-20", 5, 70)

# Single plan
plan = await planner.regenerate_single_plan("A")
```

### 3. Validate Safety

```python
from reelsbot import PolicyGate

gate = PolicyGate(config, llm_client, logger)
is_valid, reason = await gate.validate_plan(plan)

if not is_valid:
    print(f"Rejected: {reason}")
```

### 4. Generate Caption

```python
from reelsbot import CaptionGenerator

generator = CaptionGenerator(config, llm_client, logger)
caption, hashtags = await generator.generate_caption(plan)

print(f"{caption}\n\n{' '.join(f'#{tag}' for tag in hashtags)}")
```

### 5. Save to Database

```python
from reelsbot import RunStorage, ReelMetadata
from datetime import datetime
from pathlib import Path

storage = RunStorage(config, logger)

metadata = ReelMetadata(
    run_id=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    timestamp=datetime.now(),
    plan=plan,
    caption=caption,
    hashtags=hashtags,
    video_path=Path("outputs/video.mp4"),
    thumbnail_path=Path("outputs/thumb.jpg"),
)

storage.save_run(metadata)
```

### 6. Publish (DRY_RUN)

```python
from reelsbot import DryRunPublisher

publisher = DryRunPublisher(config, logger)
result = await publisher.publish(metadata)

print(f"Saved to: {result['output_dir']}")
```

---

## Model Quick Reference

### ReelPlan (A-type)

```python
plan = ReelPlan(
    type="A",
    theme="gradient",
    mood="calm",
    duration_sec=10,
    tagline="A moment of peace",
)
```

### ReelPlan (E-type)

```python
plan = ReelPlan(
    type="E",
    theme="cafe",
    mood="minimal",
    duration_sec=12,
    brand_name="WaveVoria",
    concept_title="Modern Cafe Interior",
    category="cafe",
)
```

### ReelMetadata

```python
metadata = ReelMetadata(
    run_id="unique_id",
    timestamp=datetime.now(),
    plan=plan,
    caption="Caption text",
    hashtags=["tag1", "tag2"],
    video_path=Path("video.mp4"),
    thumbnail_path=Path("thumb.jpg"),
    status="generated",  # or "failed", "published"
)
```

---

## Storage Queries

```python
storage = RunStorage(config, logger)

# Get one run
metadata = storage.get_run("run_id")

# Get recent runs
recent = storage.get_recent_runs(limit=10)

# Get by type
a_runs = storage.get_runs_by_type("A", limit=10)
e_runs = storage.get_runs_by_type("E", limit=10)

# Get by status
published = storage.get_runs_by_status("published", limit=10)

# Get statistics
stats = storage.get_stats()
print(f"Total: {stats['total']}")
print(f"By type: {stats['by_type']}")
print(f"By status: {stats['by_status']}")

# Update status
storage.update_status("run_id", "published")

# Close (optional, uses context manager)
storage.close()
```

---

## Publisher Operations

```python
publisher = DryRunPublisher(config, logger)

# Publish
result = await publisher.publish(metadata)
# Returns: {"status": "DRY_RUN", "output_dir": "...", "files": {...}}

# Check status
status = publisher.get_status("run_id")
# Returns: {"status": "exists", "output_dir": "...", "files": {...}}

# List all outputs
runs = publisher.list_runs(limit=10)

# Get output directory
output_dir = publisher.get_output_directory("run_id")

# Clean old outputs
deleted_count = publisher.clean_old_runs(keep_count=100)
```

---

## Error Handling Patterns

### Basic Try-Catch

```python
from reelsbot import PlannerError

try:
    plans = await planner.generate_daily_plan("2025-12-20", 5, 70)
except PlannerError as e:
    logger.error(f"Planning failed: {e}")
    # Handle error
```

### Retry with Regeneration

```python
from reelsbot import PolicyViolationError

max_retries = config.policy_max_retry

for attempt in range(max_retries):
    plan = await planner.regenerate_single_plan("E")
    is_valid, reason = await gate.validate_plan(plan)

    if is_valid:
        break
else:
    raise PolicyViolationError(f"Could not generate valid plan after {max_retries} attempts")
```

### Context Manager for Storage

```python
with RunStorage(config, logger) as storage:
    storage.save_run(metadata)
    # Automatically closes on exit
```

---

## Configuration Quick Tips

### Environment Variables

```bash
# .env file
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
LLM_TEMPERATURE=0.7
DEFAULT_A_RATIO=70
POLICY_MAX_RETRY=3
```

### Access in Code

```python
config = load_config()

# Get values
provider = config.llm_provider
model = config.get_active_model()
api_key = config.get_active_api_key()
a_ratio = config.default_a_ratio
```

---

## Testing Patterns

### Mock LLM Client

```python
class MockLLMClient:
    async def generate(self, system_prompt, user_prompt, **kwargs):
        return '[{"type": "A", "theme": "gradient", ...}]'

# Use in tests
planner = Planner(config, MockLLMClient(), logger)
```

### Test Plan Creation

```python
def create_test_plan(plan_type="A"):
    if plan_type == "A":
        return ReelPlan(
            type="A",
            theme="gradient",
            mood="calm",
            duration_sec=10,
            tagline="Test tagline",
        )
    else:
        return ReelPlan(
            type="E",
            theme="cafe",
            mood="minimal",
            duration_sec=12,
            brand_name="TestBrand",
            concept_title="Test Concept",
            category="cafe",
        )
```

---

## Logging Best Practices

```python
from reelsbot.utils import setup_logger

# Create logger with run_id context
logger = setup_logger("my_module", run_id="run_12345")

# Log with context
logger.info("Starting process")
logger.debug("Debug details")
logger.warning("Warning message")
logger.error("Error occurred")

# Log plan details
logger.info(f"Generated plan: {plan.get_display_title()}")
```

---

## Common Workflows

### Complete Generation Workflow

```python
async def generate_content():
    # 1. Setup
    config = load_config()
    logger = setup_logger("workflow")
    llm_client = await create_llm_client(config, logger)

    # 2. Plan
    planner = Planner(config, llm_client, logger)
    plans = await planner.generate_daily_plan("2025-12-20", 5, 70)

    # 3. Validate
    gate = PolicyGate(config, llm_client, logger)
    valid_plans = []

    for plan in plans:
        is_valid, reason = await gate.validate_plan(plan)
        if is_valid:
            valid_plans.append(plan)
        else:
            logger.warning(f"Plan rejected: {reason}")

    # 4. Generate captions
    generator = CaptionGenerator(config, llm_client, logger)
    for plan in valid_plans:
        caption, hashtags = await generator.generate_caption(plan)
        # Store or use caption
```

### Batch Processing

```python
async def batch_process(plans):
    results = []

    for plan in plans:
        try:
            # Validate
            is_valid, reason = await gate.validate_plan(plan)
            if not is_valid:
                continue

            # Generate caption
            caption, hashtags = await generator.generate_caption(plan)

            # Create metadata
            metadata = ReelMetadata(...)

            # Save
            storage.save_run(metadata)

            # Publish
            result = await publisher.publish(metadata)

            results.append(result)

        except Exception as e:
            logger.error(f"Failed to process plan: {e}")
            continue

    return results
```

---

## Performance Tips

1. **Batch LLM calls** when possible (not implemented yet, but keep in mind)
2. **Reuse clients**: Create once, use many times
3. **Use async**: All I/O operations support async/await
4. **Close storage**: Use context managers or explicit close()
5. **Cache results**: Store plans to avoid regeneration

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

logger = setup_logger("debug", level=logging.DEBUG)
```

### Inspect Plan JSON

```python
import json
print(json.dumps(plan.model_dump(), indent=2))
```

### Check Database

```python
storage = RunStorage(config, logger)
stats = storage.get_stats()
print(f"Database has {stats['total']} runs")
```

### List DRY_RUN Outputs

```python
publisher = DryRunPublisher(config, logger)
runs = publisher.list_runs()
for run in runs:
    print(f"{run['run_id']}: {run['type']}")
```

---

## File Paths Reference

```
outputs/
├── dry_run/
│   └── {run_id}/
│       ├── video.mp4
│       ├── thumbnail.jpg
│       ├── metadata.json
│       └── caption.txt
└── db/
    └── reelsbot.db

logs/
└── reelsbot_{date}.log

prompts/
├── planner_system.txt
├── policy_system.txt
└── caption_en.txt

policies/
└── blocked_terms.txt
```

---

## Type Hints Reference

```python
from typing import Literal
from pathlib import Path
from datetime import datetime

# Plan types
plan_type: Literal["A", "E"]

# Status types
status: Literal["generated", "failed", "published"]

# File paths
video_path: Path
thumbnail_path: Path

# Timestamps
timestamp: datetime

# Caption data
caption: str
hashtags: list[str]

# Validation results
is_valid: bool
reason: str

# Storage results
metadata: ReelMetadata | None
runs: list[ReelMetadata]

# Publisher results
result: dict[str, Any]
```

---

## Constants and Defaults

```python
# A-type durations
DEFAULT_A_DURATION_MIN = 8  # seconds
DEFAULT_A_DURATION_MAX = 12  # seconds

# E-type durations
DEFAULT_E_DURATION_MIN = 10  # seconds
DEFAULT_E_DURATION_MAX = 14  # seconds

# Content mix
DEFAULT_A_RATIO = 70  # percent
DEFAULT_E_RATIO = 30  # percent

# Safety
POLICY_MAX_RETRY = 3  # attempts

# LLM
LLM_TEMPERATURE = 0.7  # 0.0-2.0
LLM_MAX_TOKENS = 2000  # tokens

# Hashtags
MIN_HASHTAGS = 8
MAX_HASHTAGS = 12
```

---

This quick reference covers the most common use cases for Phase 2 modules. For detailed API documentation, see `README_PHASE2.md`.
