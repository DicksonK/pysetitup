"""Logging configuration with Rich formatting."""

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Custom theme with Catppuccin Mocha colors
CATPPUCCIN_THEME = Theme(
    {
        "info": "bold cyan",
        "warning": "bold yellow",
        "error": "bold red",
        "critical": "bold white on red",
        "success": "bold green",
        "debug": "dim cyan",
    }
)

# Global console instance
console = Console(theme=CATPPUCCIN_THEME)


def setup_logging(level: int = logging.INFO, verbose: bool = False) -> None:
    """
    Configure logging with Rich formatting.

    Args:
        level: Logging level (default: INFO)
        verbose: If True, enable DEBUG level logging
    """
    if verbose:
        level = logging.DEBUG

    # Configure Rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
    )

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler],
    )

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"✓ {message}", style="success")


def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"✗ {message}", style="error")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"⚠ {message}", style="warning")


def print_info(message: str) -> None:
    """Print an info message in cyan."""
    console.print(f"ℹ {message}", style="info")


def print_step(step: int, total: int, message: str) -> None:
    """
    Print a step indicator.

    Args:
        step: Current step number
        total: Total number of steps
        message: Step description
    """
    console.print(f"\n[bold cyan]Step {step}/{total}:[/bold cyan] {message}")
