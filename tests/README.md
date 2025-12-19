# Reelsbot Test Suite Documentation

Comprehensive test documentation for the reelsbot Instagram Reels automation system.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Coverage Reports](#coverage-reports)
- [Writing Tests](#writing-tests)
- [Mocking Strategies](#mocking-strategies)
- [Troubleshooting](#troubleshooting)

## Overview

The reelsbot test suite provides comprehensive coverage across all system components:

- **Unit Tests**: Isolated component testing with mocked dependencies
- **Integration Tests**: Multi-component workflow testing
- **End-to-End Tests**: Complete pipeline validation

**Current Test Coverage**: Target 90%+ across all modules

### Key Test Files

```
tests/
├── conftest.py                   # Shared fixtures and test utilities
├── test_cli.py                   # CLI command tests
├── test_orchestrator.py          # Pipeline orchestration tests
├── test_e2e_integration.py       # End-to-end workflow tests
├── test_phase3_integration.py    # Video generation tests
├── test_config.py                # Configuration tests
├── test_llm_client.py            # LLM client tests
└── [other component tests...]
```

## Test Structure

### Test Organization

Tests are organized by component and test type:

```python
# Unit tests - isolated component
@pytest.mark.unit
def test_component_initialization():
    pass

# Integration tests - multiple components
@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_workflow():
    pass

# End-to-end tests - complete system
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_pipeline():
    pass
```

### Fixtures

Common fixtures are defined in `conftest.py`:

- `test_config`: Test configuration
- `test_logger`: Test logger instance
- `temp_dir`: Temporary directory for outputs
- `mock_llm_client`: Mocked LLM client
- `sample_plan_A`: Sample A-type plan
- `sample_plan_E`: Sample E-type plan
- `sample_metadata_A`: Sample A-type metadata
- `sample_metadata_E`: Sample E-type metadata

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=src/reelsbot --cov-report=html --cov-report=term
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# End-to-end tests only
pytest -m e2e

# Exclude slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Run CLI tests
pytest tests/test_cli.py

# Run orchestrator tests
pytest tests/test_orchestrator.py

# Run e2e tests
pytest tests/test_e2e_integration.py
```

### Run Specific Test Functions

```bash
# Run single test
pytest tests/test_cli.py::test_cli_help

# Run tests matching pattern
pytest -k "test_pipeline"
```

### Verbose Output

```bash
# Show detailed output
pytest -v

# Show print statements
pytest -s

# Show detailed failure info
pytest -vv
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution (<100ms each)
- Mocked dependencies
- No external API calls
- No file I/O (use temp dirs)

**Example**:
```python
@pytest.mark.unit
def test_config_loading(test_config):
    assert test_config.llm_provider == "openai"
    assert test_config.video_fps == 30
```

### Integration Tests (`@pytest.mark.integration`)

**Purpose**: Test interactions between multiple components

**Characteristics**:
- Moderate execution time
- May use real components with mocked external services
- Tests workflows across multiple modules

**Example**:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_plan_validation_workflow(test_config, test_logger):
    planner = Planner(config, llm_client, logger)
    policy_gate = PolicyGate(config, llm_client, logger)

    plan = await planner.generate_abstract_plan()
    result = await policy_gate.validate(plan)

    assert result["is_valid"] is True
```

### End-to-End Tests (`@pytest.mark.e2e`)

**Purpose**: Test complete pipeline from start to finish

**Characteristics**:
- Slower execution (may take seconds)
- Tests entire workflow
- Validates file outputs and structure
- Verifies cross-component integration

**Example**:
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_pipeline_A_type(orchestrator, temp_dir):
    results = await orchestrator.run_pipeline(
        count=1, type_filter="A", dry_run=True
    )

    assert len(results) == 1
    assert results[0].video_path.exists()
    assert results[0].thumbnail_path.exists()
```

### Slow Tests (`@pytest.mark.slow`)

**Purpose**: Mark tests that take significant time

**Usage**: Skip during rapid development
```bash
pytest -m "not slow"
```

## Coverage Reports

### Generate Coverage Report

```bash
# Generate HTML and terminal reports
pytest --cov=src/reelsbot --cov-report=html --cov-report=term-missing
```

### View HTML Coverage Report

```bash
# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

### Coverage Report Location

- **HTML**: `htmlcov/index.html`
- **JSON**: `coverage.json`
- **Terminal**: Displayed after test run

### Target Coverage

| Module | Target | Priority |
|--------|--------|----------|
| orchestrator.py | 95%+ | Critical |
| planner.py | 90%+ | High |
| policy_gate.py | 95%+ | Critical |
| cli.py | 90%+ | High |
| generator/ | 85%+ | Medium |
| editor/ | 85%+ | Medium |
| utils/ | 80%+ | Medium |

## Writing Tests

### Test Naming Convention

```python
# Pattern: test_<component>_<behavior>_<condition>
def test_planner_generates_abstract_plan_successfully():
    pass

def test_policy_gate_rejects_blocked_terms():
    pass

def test_cli_run_command_with_type_filter():
    pass
```

### Using Fixtures

```python
import pytest

def test_with_fixtures(test_config, sample_plan_A, temp_dir):
    """Test using multiple fixtures."""
    # Fixtures are automatically injected
    assert test_config.llm_provider == "openai"
    assert sample_plan_A.type == "A"
    assert temp_dir.exists()
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function(mock_llm_client):
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("plan_type,expected_duration", [
    ("A", 10),
    ("E", 12),
])
def test_plan_duration(plan_type, expected_duration):
    """Test different plan types."""
    assert get_duration(plan_type) == expected_duration
```

## Mocking Strategies

### Mocking LLM Client

```python
def test_with_mock_llm(mock_llm_client):
    """Mock LLM returns canned responses."""
    # mock_llm_client automatically returns valid JSON
    planner = Planner(config, mock_llm_client, logger)
    # No real API calls made
```

### Mocking FFmpeg

```python
@patch("reelsbot.utils.ffmpeg.run_ffmpeg_command")
def test_video_generation(mock_ffmpeg):
    """Mock FFmpeg to avoid actual video processing."""
    generator = FFmpegDummyGenerator(config, logger)

    # Create dummy output file
    def mock_side_effect(cmd, *args, **kwargs):
        # Extract output path and create dummy file
        pass

    mock_ffmpeg.side_effect = mock_side_effect
```

### Mocking File I/O

```python
def test_with_temp_files(temp_dir):
    """Use temp_dir fixture for file operations."""
    # All files created in temp_dir
    video_path = temp_dir / "video.mp4"
    video_path.touch()

    # Automatically cleaned up after test
    assert video_path.exists()
```

### Mocking External APIs

```python
@patch("reelsbot.llm_client.OpenAI")
def test_without_real_api(mock_openai):
    """Mock external API client."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # No real API calls
```

## Testing Without FFmpeg

If FFmpeg is not installed, tests will mock FFmpeg calls:

```python
@pytest.fixture
def mock_ffmpeg_command(mocker):
    """Mock FFmpeg for environments without installation."""
    return mocker.patch("reelsbot.utils.ffmpeg.run_ffmpeg_command")
```

To run tests without FFmpeg:
```bash
# All video generation tests mock FFmpeg by default
pytest
```

## Testing Without LLM API Key

Tests use mocked LLM client by default:

```python
# No API key required - uses mock responses
pytest

# Mock LLM client fixture provides canned responses
def test_planning(mock_llm_client):
    # No real API calls
    planner = Planner(config, mock_llm_client, logger)
```

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'reelsbot'`
```bash
# Solution: Install package in editable mode
pip install -e .
```

**Issue**: `FileNotFoundError` in tests
```bash
# Solution: Use temp_dir fixture
def test_with_files(temp_dir):
    file_path = temp_dir / "test.txt"
    file_path.touch()
```

**Issue**: Async tests not running
```bash
# Solution: Add @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async():
    result = await async_function()
```

**Issue**: Tests fail with API errors
```bash
# Solution: Ensure mocks are applied
def test_with_mock(mock_llm_client):
    # Use mock fixture
    pass
```

### Debugging Tests

```bash
# Run with debugger
pytest --pdb

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Increase verbosity
pytest -vv
```

### Test Performance

```bash
# Show slowest tests
pytest --durations=10

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

## Continuous Integration

Tests are designed for CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=src/reelsbot --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Test Maintenance

### Adding New Tests

1. Create test file: `tests/test_<module>.py`
2. Import fixtures from `conftest.py`
3. Use appropriate markers (`@pytest.mark.unit`, etc.)
4. Follow naming conventions
5. Mock external dependencies
6. Run tests and verify coverage

### Updating Fixtures

Edit `tests/conftest.py` to add/modify shared fixtures:

```python
@pytest.fixture
def new_fixture():
    """New shared fixture."""
    return some_test_object
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Fast**: Keep unit tests under 100ms
3. **Clear**: Use descriptive test names
4. **Assertions**: Use specific assertions, not `assert True`
5. **Fixtures**: Reuse fixtures to avoid duplication
6. **Mocking**: Mock external dependencies (API, FFmpeg)
7. **Cleanup**: Use temp directories (auto-cleanup)
8. **Documentation**: Add docstrings to complex tests

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Contact

For test-related questions or issues, refer to:
- Main project README: `README.md`
- Project documentation: `docs/`
- Quick start guide: `QUICK_START_GUIDE.md`
