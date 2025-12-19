"""Entry point for running reelsbot as a module.

This allows running the CLI with:
    python -m reelsbot [command] [options]
"""

from reelsbot.cli import cli

if __name__ == '__main__':
    cli()
