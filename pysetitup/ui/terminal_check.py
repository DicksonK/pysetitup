"""Terminal size validation utilities."""

import shutil
import sys
from typing import Optional

from rich.console import Console


MIN_TERMINAL_WIDTH = 140
MIN_TERMINAL_HEIGHT = 30


def check_terminal_size() -> bool:
    """
    Check if terminal is large enough for the TUI.

    Returns:
        True if terminal meets minimum size requirements, False otherwise.
    """
    try:
        terminal_size = shutil.get_terminal_size()
        return (terminal_size.columns >= MIN_TERMINAL_WIDTH and
                terminal_size.lines >= MIN_TERMINAL_HEIGHT)
    except Exception:
        # If we can't determine size, proceed anyway
        return True


def show_terminal_size_error(console: Optional[Console] = None, use_rich: bool = True) -> None:
    """
    Display terminal size error message and exit.

    Args:
        console: Optional Rich console instance for formatted output.
                 If not provided, a new one will be created.
        use_rich: Whether to use Rich formatting (True) or plain text (False).
    """
    if use_rich and console is None:
        console = Console()

    try:
        terminal_size = shutil.get_terminal_size()
        current_width = terminal_size.columns
        current_height = terminal_size.lines
    except Exception:
        current_width = None
        current_height = None

    # Build error message
    if use_rich and console:
        console.print("[red]❌ Error: Terminal size is too small for the TUI.[/red]")
        console.print(f"   Minimum required: {MIN_TERMINAL_WIDTH} columns × {MIN_TERMINAL_HEIGHT} lines")

        if current_width and current_height:
            console.print(f"   Current size: {current_width} columns × {current_height} lines")

            if current_width < MIN_TERMINAL_WIDTH:
                console.print(f"   → Need {MIN_TERMINAL_WIDTH - current_width} more columns")
            if current_height < MIN_TERMINAL_HEIGHT:
                console.print(f"   → Need {MIN_TERMINAL_HEIGHT - current_height} more lines")

        console.print(f"\n   Please resize your terminal to at least {MIN_TERMINAL_WIDTH}×{MIN_TERMINAL_HEIGHT}.")
    else:
        # Plain text output
        print(f"❌ Error: Terminal size is too small for the TUI.")
        print(f"   Minimum required: {MIN_TERMINAL_WIDTH} columns × {MIN_TERMINAL_HEIGHT} lines")

        if current_width and current_height:
            print(f"   Current size: {current_width} columns × {current_height} lines")

            if current_width < MIN_TERMINAL_WIDTH:
                print(f"   → Need {MIN_TERMINAL_WIDTH - current_width} more columns")
            if current_height < MIN_TERMINAL_HEIGHT:
                print(f"   → Need {MIN_TERMINAL_HEIGHT - current_height} more lines")

        print(f"\n   Please resize your terminal to at least {MIN_TERMINAL_WIDTH}×{MIN_TERMINAL_HEIGHT}.")

    sys.exit(1)


def check_and_enforce_terminal_size(console: Optional[Console] = None, use_rich: bool = True) -> None:
    """
    Check terminal size and exit with error message if too small.

    This is a convenience function that combines check_terminal_size()
    and show_terminal_size_error().

    Args:
        console: Optional Rich console instance for formatted output.
        use_rich: Whether to use Rich formatting (True) or plain text (False).
    """
    if not check_terminal_size():
        show_terminal_size_error(console=console, use_rich=use_rich)
