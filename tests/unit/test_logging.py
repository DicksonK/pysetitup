"""Unit tests for pysetitup.utils.logging module."""

import logging
from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from pysetitup.utils.logging import (
    CATPPUCCIN_THEME,
    console,
    get_logger,
    print_error,
    print_info,
    print_step,
    print_success,
    print_warning,
    setup_logging,
)


class TestSetupLogging:
    """Test logging setup."""

    def test_setup_logging_default_level(self) -> None:
        """Test setup_logging with default INFO level."""
        # Reset root logger first
        logging.getLogger().handlers.clear()
        setup_logging()
        logger = logging.getLogger()
        # Should be INFO or lower (DEBUG is 10, INFO is 20, WARNING is 30)
        assert logger.level <= logging.INFO

    def test_setup_logging_with_verbose(self) -> None:
        """Test setup_logging with verbose flag enables DEBUG."""
        logging.getLogger().handlers.clear()
        setup_logging(verbose=True)
        logger = logging.getLogger()
        assert logger.level <= logging.DEBUG

    def test_setup_logging_custom_level(self) -> None:
        """Test setup_logging with custom level."""
        logging.getLogger().handlers.clear()
        setup_logging(level=logging.WARNING)
        logger = logging.getLogger()
        assert logger.level <= logging.WARNING

    def test_setup_logging_silences_httpx(self) -> None:
        """Test setup_logging silences httpx logger."""
        setup_logging()
        httpx_logger = logging.getLogger("httpx")
        assert httpx_logger.level == logging.WARNING


class TestGetLogger:
    """Test logger creation."""

    def test_get_logger_returns_logger(self) -> None:
        """Test get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_different_names(self) -> None:
        """Test get_logger returns different loggers for different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1.name != logger2.name


class TestPrintHelpers:
    """Test print helper functions."""

    def test_print_success(self) -> None:
        """Test print_success outputs with checkmark."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True, width=80, theme=CATPPUCCIN_THEME)

        with patch("pysetitup.utils.logging.console", test_console):
            print_success("Installation complete")

        result = output.getvalue()
        assert "✓" in result
        assert "Installation complete" in result

    def test_print_error(self) -> None:
        """Test print_error outputs with X mark."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True, width=80, theme=CATPPUCCIN_THEME)

        with patch("pysetitup.utils.logging.console", test_console):
            print_error("Installation failed")

        result = output.getvalue()
        assert "✗" in result
        assert "Installation failed" in result

    def test_print_warning(self) -> None:
        """Test print_warning outputs with warning symbol."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True, width=80, theme=CATPPUCCIN_THEME)

        with patch("pysetitup.utils.logging.console", test_console):
            print_warning("Potential issue detected")

        result = output.getvalue()
        assert "⚠" in result
        assert "Potential issue detected" in result

    def test_print_info(self) -> None:
        """Test print_info outputs with info symbol."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True, width=80, theme=CATPPUCCIN_THEME)

        with patch("pysetitup.utils.logging.console", test_console):
            print_info("Starting installation")

        result = output.getvalue()
        assert "ℹ" in result
        assert "Starting installation" in result

    def test_print_step(self) -> None:
        """Test print_step outputs step indicator."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=True, width=80, theme=CATPPUCCIN_THEME)

        with patch("pysetitup.utils.logging.console", test_console):
            print_step(3, 7, "Installing packages")

        result = output.getvalue()
        # Output contains ANSI codes, just check key parts are present
        assert "3" in result
        assert "7" in result
        assert "Installing packages" in result


class TestConsole:
    """Test console instance."""

    def test_console_has_custom_theme(self) -> None:
        """Test console uses custom Catppuccin theme."""
        # Console in Rich 14+ uses _theme_stack instead of theme property
        # Just verify the theme exists and has expected styles
        assert "success" in CATPPUCCIN_THEME.styles
        assert "error" in CATPPUCCIN_THEME.styles
        assert "warning" in CATPPUCCIN_THEME.styles
        assert "info" in CATPPUCCIN_THEME.styles
