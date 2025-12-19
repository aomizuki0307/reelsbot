"""Command-line interface for the reelsbot Instagram Reels automation system.

This module provides a Click-based CLI with commands for planning, generating,
validating, and managing Instagram Reels content.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from reelsbot import __version__
from reelsbot.config import load_config
from reelsbot.models import ReelMetadata, ReelPlan
from reelsbot.orchestrator import Orchestrator
from reelsbot.planner import Planner
from reelsbot.policy_gate import PolicyGate
from reelsbot.llm_client import create_llm_client
from reelsbot.utils import setup_logger


# Color schemes for output
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print a styled header."""
    click.echo()
    click.echo(click.style(text, fg='bright_cyan', bold=True))
    click.echo(click.style("=" * len(text), fg='cyan'))
    click.echo()


def print_success(text: str) -> None:
    """Print a success message."""
    click.echo(click.style(f"[OK] {text}", fg='green'))


def print_error(text: str) -> None:
    """Print an error message."""
    click.echo(click.style(f"[ERROR] {text}", fg='red'), err=True)


def print_warning(text: str) -> None:
    """Print a warning message."""
    click.echo(click.style(f"[WARNING] {text}", fg='yellow'))


def print_info(text: str) -> None:
    """Print an info message."""
    click.echo(click.style(f"[INFO] {text}", fg='blue'))


def print_step(step: int, total: int, text: str) -> None:
    """Print a step indicator."""
    click.echo(click.style(f"[{step}/{total}] {text}", fg='cyan'))


@click.group()
@click.version_option(version=__version__, prog_name="reelsbot")
def cli():
    """Reelsbot - Instagram Reels automation tool.

    Automated content generation for Instagram Reels with AI-powered planning,
    video generation, caption writing, and policy compliance.

    \b
    Features:
    - Abstract (A) and Educational (E) content types
    - LLM-powered content planning and caption generation
    - Policy-based content validation
    - FFmpeg-based video generation and editing
    - Dry-run mode for testing

    \b
    Examples:
        # Generate daily posting plan
        python -m reelsbot plan --count 7 --ratio 70:30

        # Generate a single A-type video
        python -m reelsbot run --count 1 --type A --dry-run

        # Generate multiple videos with mixed ratio
        python -m reelsbot run --count 7 --mix --dry-run

        # Validate metadata
        python -m reelsbot validate outputs/run_20251220_123456/metadata_1.json
    """
    pass


@cli.command()
@click.option(
    '--date',
    default=None,
    help='Plan date (YYYY-MM-DD). Default: today.',
)
@click.option(
    '--count',
    default=7,
    type=int,
    help='Number of posts to plan. Default: 7.',
)
@click.option(
    '--ratio',
    default="70:30",
    help='A:E ratio (e.g., "70:30"). Default: 70:30.',
)
@click.option(
    '--output',
    type=click.Path(),
    default=None,
    help='Save plan to JSON file (optional).',
)
def plan(date: Optional[str], count: int, ratio: str, output: Optional[str]):
    """Generate daily posting plan.

    Creates a content plan with the specified A/E ratio, showing what type
    of content will be posted and when. The plan can be saved to a JSON file
    for later execution.

    \b
    Examples:
        # Generate 7-day plan with default ratio
        python -m reelsbot plan --count 7

        # Generate custom plan and save to file
        python -m reelsbot plan --count 5 --ratio 60:40 --output plan.json

        # Generate plan for specific date
        python -m reelsbot plan --date 2025-12-25 --count 7
    """
    print_header("Reelsbot - Content Planning")

    try:
        # Parse ratio
        try:
            a_ratio, e_ratio = map(int, ratio.split(':'))
            if a_ratio + e_ratio != 100:
                raise ValueError("Ratio must sum to 100")
        except Exception as e:
            print_error(f"Invalid ratio format: {ratio}. Use format like '70:30'")
            sys.exit(1)

        # Parse date if provided
        plan_date = None
        if date:
            try:
                plan_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                print_error(f"Invalid date format: {date}. Use YYYY-MM-DD")
                sys.exit(1)
        else:
            plan_date = datetime.now()

        # Load config
        print_info(f"Loading configuration...")
        config = load_config()

        # Override ratio in config if provided
        config.default_a_ratio = a_ratio
        config.default_e_ratio = e_ratio

        # Setup logger
        run_id = f"plan_{plan_date.strftime('%Y%m%d')}"
        logger = setup_logger(run_id, config.logs_dir)

        # Create planner
        llm_client = create_llm_client(config)
        planner = Planner(config=config, llm_client=llm_client, logger=logger)

        # Generate plan
        print_info(f"Generating plan for {plan_date.strftime('%Y-%m-%d')} with {count} posts...")
        print_info(f"Ratio: {a_ratio}% Abstract, {e_ratio}% Educational")

        plans = asyncio.run(planner.generate_daily_plan(count=count))

        # Display plan
        click.echo()
        click.echo(click.style("Generated Content Plan:", bold=True))
        click.echo()

        for idx, plan_item in enumerate(plans, 1):
            type_str = click.style(f"[{plan_item.type}]", fg='green' if plan_item.type == 'A' else 'blue', bold=True)
            title = plan_item.get_display_title()
            duration = f"{plan_item.duration_sec}s"
            mood = plan_item.mood

            click.echo(f"  {idx}. {type_str} {title}")
            click.echo(f"     Duration: {duration}, Mood: {mood}")
            click.echo()

        # Count by type
        a_count = sum(1 for p in plans if p.type == "A")
        e_count = sum(1 for p in plans if p.type == "E")

        click.echo(click.style(f"Summary: {a_count} Abstract, {e_count} Educational", bold=True))
        click.echo()

        # Save to file if requested
        if output:
            output_path = Path(output)
            plans_data = [plan_item.model_dump() for plan_item in plans]

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': plan_date.strftime('%Y-%m-%d'),
                    'count': count,
                    'ratio': ratio,
                    'plans': plans_data,
                }, f, indent=2, ensure_ascii=False)

            print_success(f"Plan saved to: {output_path.absolute()}")

        print_success(f"Planning complete!")

    except Exception as e:
        print_error(f"Planning failed: {e}")
        logger.error(f"Planning failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--count',
    default=1,
    type=int,
    help='Number of videos to generate. Default: 1.',
)
@click.option(
    '--type',
    'type_filter',
    type=click.Choice(['A', 'E'], case_sensitive=True),
    help='Video type: A (abstract) or E (educational). Mutually exclusive with --mix.',
)
@click.option(
    '--mix',
    is_flag=True,
    help='Use A/E ratio from config. Mutually exclusive with --type.',
)
@click.option(
    '--dry-run/--live',
    default=True,
    help='DRY_RUN mode (local save only) or LIVE mode. Default: dry-run.',
)
def run(count: int, type_filter: Optional[str], mix: bool, dry_run: bool):
    """Generate and publish Instagram Reels.

    Creates videos based on content plans, applies overlays, generates captions,
    and publishes to Instagram (or saves locally in dry-run mode).

    \b
    Examples:
        # Generate 1 abstract video (dry-run)
        python -m reelsbot run --count 1 --type A

        # Generate 1 educational video (dry-run)
        python -m reelsbot run --count 1 --type E

        # Generate 7 videos with mixed ratio
        python -m reelsbot run --count 7 --mix

        # Generate and publish live (requires Instagram credentials)
        python -m reelsbot run --count 1 --type A --live
    """
    print_header("Reelsbot - Video Generation")

    try:
        # Validate mutually exclusive options
        if type_filter and mix:
            print_error("Cannot specify both --type and --mix")
            sys.exit(1)

        # Load config
        print_info("Loading configuration...")
        config = load_config()

        # Setup logger (temporary run_id, will be updated by orchestrator)
        temp_run_id = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger = setup_logger(temp_run_id, config.logs_dir)

        # Create orchestrator
        print_info("Initializing orchestrator...")
        orchestrator = Orchestrator(config=config, logger=logger)

        # Display run parameters
        click.echo()
        if type_filter:
            type_name = "Abstract" if type_filter == "A" else "Educational"
            click.echo(click.style(f"Generating {count} {type_name} ({type_filter}-type) video(s)...", bold=True))
        elif mix:
            click.echo(click.style(
                f"Generating {count} video(s) with {config.default_a_ratio}:{config.default_e_ratio} A:E ratio...",
                bold=True
            ))
        else:
            click.echo(click.style(f"Generating {count} video(s) (default type)...", bold=True))

        mode = click.style("DRY_RUN", fg='yellow') if dry_run else click.style("LIVE", fg='red', bold=True)
        click.echo(f"Mode: {mode}")
        click.echo()

        # Run pipeline
        print_info("Starting pipeline execution...")

        metadata_list = asyncio.run(
            orchestrator.run_pipeline(
                count=count,
                type_filter=type_filter,
                mix=mix,
                dry_run=dry_run,
            )
        )

        # Display results
        click.echo()
        click.echo(click.style("=" * 60, fg='cyan'))
        click.echo()

        if metadata_list:
            print_success(f"Complete! {len(metadata_list)} video(s) generated.")
            click.echo()

            for idx, metadata in enumerate(metadata_list, 1):
                click.echo(click.style(f"Video {idx}:", bold=True))
                click.echo(f"  Type: {metadata.plan.type}")
                click.echo(f"  Title: {metadata.plan.get_display_title()}")
                click.echo(f"  Video: {metadata.video_path}")
                click.echo(f"  Thumbnail: {metadata.thumbnail_path}")
                click.echo(f"  Caption: {metadata.caption[:60]}...")
                click.echo()

            # Show output directory
            if metadata_list:
                output_dir = metadata_list[0].video_path.parent
                click.echo(click.style(f"Output directory: {output_dir.absolute()}", bold=True))
        else:
            print_warning("No videos were generated successfully")

    except KeyboardInterrupt:
        print_warning("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Generation failed: {e}")
        logger.error(f"Generation failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument(
    'metadata_path',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def validate(metadata_path: Path):
    """Re-validate metadata against policy.

    Loads a previously generated metadata file and validates it against
    the current policy rules. Useful for checking if content still meets
    policy requirements after policy updates.

    \b
    Examples:
        # Validate a single metadata file
        python -m reelsbot validate outputs/run_20251220_123456/metadata_1.json

        # Validate all metadata in a run directory
        for file in outputs/run_*/metadata_*.json; do
            python -m reelsbot validate "$file"
        done
    """
    print_header("Reelsbot - Metadata Validation")

    try:
        # Load metadata
        print_info(f"Loading metadata from: {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata_data = json.load(f)

        # Parse into ReelMetadata
        metadata = ReelMetadata(**metadata_data)

        click.echo()
        click.echo(click.style("Metadata Details:", bold=True))
        click.echo(f"  Run ID: {metadata.run_id}")
        click.echo(f"  Type: {metadata.plan.type}")
        click.echo(f"  Title: {metadata.plan.get_display_title()}")
        click.echo(f"  Status: {metadata.status}")
        click.echo()

        # Load config and setup for validation
        print_info("Loading configuration...")
        config = load_config()

        # Setup logger
        logger = setup_logger(f"validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}", config.logs_dir)

        # Create policy gate
        llm_client = create_llm_client(config)
        policy_gate = PolicyGate(config=config, llm_client=llm_client, logger=logger)

        # Validate
        print_info("Validating against policy...")

        result = asyncio.run(policy_gate.validate(metadata.plan))

        click.echo()
        click.echo(click.style("=" * 60, fg='cyan'))
        click.echo()

        if result["is_valid"]:
            print_success("Validation PASSED")
            click.echo()
            click.echo(click.style("Content meets all policy requirements.", fg='green'))
        else:
            print_error("Validation FAILED")
            click.echo()
            click.echo(click.style("Policy Violations:", fg='red', bold=True))

            violations = result.get("violations", [])
            if violations:
                for violation in violations:
                    click.echo(f"  • {violation}")
            else:
                click.echo(f"  • {result.get('reason', 'Unknown reason')}")

            click.echo()
            print_warning("Content does not meet policy requirements")
            sys.exit(1)

    except FileNotFoundError:
        print_error(f"Metadata file not found: {metadata_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in metadata file: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Validation failed: {e}")
        sys.exit(1)


@cli.command()
def info():
    """Display system information and configuration.

    Shows current configuration settings, available models, and system status.
    """
    print_header("Reelsbot - System Information")

    try:
        config = load_config()

        click.echo(click.style("Configuration:", bold=True))
        click.echo(f"  Version: {__version__}")
        click.echo(f"  LLM Provider: {config.llm_provider}")
        click.echo(f"  Model: {config.get_active_model()}")
        click.echo(f"  Video Resolution: {config.video_resolution[0]}x{config.video_resolution[1]}")
        click.echo(f"  FPS: {config.video_fps}")
        click.echo(f"  A/E Ratio: {config.default_a_ratio}:{config.default_e_ratio}")
        click.echo()

        click.echo(click.style("Duration Ranges:", bold=True))
        click.echo(f"  Abstract (A): {config.default_a_duration_min}-{config.default_a_duration_max}s")
        click.echo(f"  Educational (E): {config.default_e_duration_min}-{config.default_e_duration_max}s")
        click.echo()

        click.echo(click.style("Paths:", bold=True))
        click.echo(f"  Outputs: {config.outputs_dir.absolute()}")
        click.echo(f"  Logs: {config.logs_dir.absolute()}")
        click.echo(f"  FFmpeg: {config.ffmpeg_path}")
        click.echo()

        click.echo(click.style("Policy:", bold=True))
        click.echo(f"  Max Retries: {config.policy_max_retry}")
        click.echo(f"  Blocked Terms: {config.blocked_terms_path}")
        click.echo()

        print_success("Configuration loaded successfully")

    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
