"""Entry point for PySetItUp CLI."""

import sys


def main() -> None:
    """Main entry point for the PySetItUp CLI application."""
    # Import here to speed up --help and --version
    from pysetitup.cli.main import app

    app()


if __name__ == "__main__":
    sys.exit(main())
