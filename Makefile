# Makefile for reelsbot - Instagram Reels automation tool
# Windows-compatible using PowerShell and Python commands

.PHONY: help setup install test lint format clean run-demo check-uv check-python check-ffmpeg

# Default target
help:
	@echo.
	@echo ============================================================
	@echo reelsbot - Instagram Reels automation tool
	@echo ============================================================
	@echo.
	@echo Available targets:
	@echo   make setup       - Install dependencies with uv
	@echo   make install     - Install package in development mode
	@echo   make test        - Run pytest with coverage
	@echo   make lint        - Run ruff and mypy checks
	@echo   make format      - Format code with black and ruff
	@echo   make clean       - Clean outputs, logs, and cache
	@echo   make run-demo    - Run demo (1 A + 1 E video)
	@echo   make check-deps  - Check all dependencies (Python, FFmpeg, uv)
	@echo.

# Check if Python 3.10+ is installed
check-python:
	@python --version 2>nul || (echo [ERROR] Python not found. Please install Python 3.10+. && exit 1)
	@python -c "import sys; v=sys.version_info; exit(0 if v.major==3 and v.minor>=10 else 1)" || (echo [ERROR] Python 3.10+ required. && exit 1)
	@echo [OK] Python version check passed

# Check if uv is installed
check-uv:
	@uv --version 2>nul || (echo [ERROR] uv not found. Install: pip install uv && exit 1)
	@echo [OK] uv is installed

# Check if FFmpeg is installed
check-ffmpeg:
	@ffmpeg -version 2>nul || (echo [WARNING] FFmpeg not found in PATH. Install from https://ffmpeg.org/ && exit 1)
	@echo [OK] FFmpeg is installed

# Check all dependencies
check-deps: check-python check-uv check-ffmpeg
	@echo [OK] All dependencies are installed

# Setup virtual environment and install dependencies
setup: check-python check-uv
	@echo [INFO] Setting up reelsbot development environment...
	@if not exist .venv (uv venv .venv) else (echo [INFO] Virtual environment already exists)
	@echo [INFO] Installing dependencies...
	@uv pip install -e ".[dev]"
	@echo [INFO] Creating required directories...
	@if not exist outputs mkdir outputs
	@if not exist logs mkdir logs
	@if not exist policies mkdir policies
	@echo [INFO] Checking for .env file...
	@if not exist .env (copy .env.example .env && echo [WARNING] Created .env from .env.example. Please configure API keys!) else (echo [OK] .env file exists)
	@echo [OK] Setup complete! Run 'make check-deps' to verify FFmpeg installation.

# Install package in editable mode
install: check-python
	@echo [INFO] Installing reelsbot in development mode...
	@if not exist .venv (echo [ERROR] Virtual environment not found. Run 'make setup' first. && exit 1)
	@uv pip install -e ".[dev]"
	@echo [OK] Installation complete

# Run tests with coverage
test:
	@echo [INFO] Running tests with coverage...
	@if not exist .venv (echo [ERROR] Virtual environment not found. Run 'make setup' first. && exit 1)
	@python -m pytest
	@echo [OK] Tests complete. Coverage report generated in htmlcov/

# Run linting checks
lint:
	@echo [INFO] Running linting checks...
	@if not exist .venv (echo [ERROR] Virtual environment not found. Run 'make setup' first. && exit 1)
	@echo [INFO] Running ruff check...
	@python -m ruff check src/ tests/
	@echo [INFO] Running mypy type checking...
	@python -m mypy src/reelsbot --ignore-missing-imports
	@echo [OK] Linting complete

# Format code with black and ruff
format:
	@echo [INFO] Formatting code...
	@if not exist .venv (echo [ERROR] Virtual environment not found. Run 'make setup' first. && exit 1)
	@echo [INFO] Running black formatter...
	@python -m black src/ tests/
	@echo [INFO] Running ruff auto-fix...
	@python -m ruff check --fix src/ tests/
	@echo [OK] Formatting complete

# Clean generated files and caches
clean:
	@echo [INFO] Cleaning outputs, logs, and cache files...
	@if exist outputs rmdir /s /q outputs
	@if exist logs rmdir /s /q logs
	@if exist htmlcov rmdir /s /q htmlcov
	@if exist .coverage del .coverage
	@if exist coverage.json del coverage.json
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist .ruff_cache rmdir /s /q .ruff_cache
	@if exist .mypy_cache rmdir /s /q .mypy_cache
	@for /r %%i in (__pycache__) do @if exist "%%i" rmdir /s /q "%%i"
	@for /r %%i in (*.pyc) do @if exist "%%i" del "%%i"
	@for /r %%i in (*.pyo) do @if exist "%%i" del "%%i"
	@echo [INFO] Recreating empty directories...
	@mkdir outputs
	@mkdir logs
	@echo [OK] Cleanup complete

# Run demo: generate 1 A-type and 1 E-type video
run-demo:
	@echo [INFO] Running reelsbot demo...
	@if not exist .venv (echo [ERROR] Virtual environment not found. Run 'make setup' first. && exit 1)
	@echo [INFO] Checking .env configuration...
	@if not exist .env (echo [ERROR] .env file not found. Run 'make setup' first. && exit 1)
	@echo.
	@echo ============================================================
	@echo Generating 1 Abstract (A-type) video...
	@echo ============================================================
	@echo.
	@python -m reelsbot run --count 1 --type A --dry-run
	@echo.
	@echo ============================================================
	@echo Generating 1 Educational (E-type) video...
	@echo ============================================================
	@echo.
	@python -m reelsbot run --count 1 --type E --dry-run
	@echo.
	@echo [OK] Demo complete! Check outputs/ directory for generated videos.

# Quick start: setup + run demo
quickstart: setup run-demo
	@echo [OK] Quick start complete!
