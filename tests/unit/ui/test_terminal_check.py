"""Tests for terminal size validation utilities."""

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from pysetitup.ui.terminal_check import (
    MIN_TERMINAL_HEIGHT,
    MIN_TERMINAL_WIDTH,
    check_and_enforce_terminal_size,
    check_terminal_size,
    show_terminal_size_error,
)


class TestCheckTerminalSize:
    """Test the check_terminal_size function."""

    def test_terminal_size_meets_requirements(self) -> None:
        """Test returns True when terminal meets minimum size."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH,
                lines=MIN_TERMINAL_HEIGHT,
            )
            assert check_terminal_size() is True

    def test_terminal_size_exceeds_requirements(self) -> None:
        """Test returns True when terminal exceeds minimum size."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH + 50,
                lines=MIN_TERMINAL_HEIGHT + 20,
            )
            assert check_terminal_size() is True

    def test_terminal_width_too_small(self) -> None:
        """Test returns False when terminal width is too small."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 1,
                lines=MIN_TERMINAL_HEIGHT,
            )
            assert check_terminal_size() is False

    def test_terminal_height_too_small(self) -> None:
        """Test returns False when terminal height is too small."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH,
                lines=MIN_TERMINAL_HEIGHT - 1,
            )
            assert check_terminal_size() is False

    def test_terminal_both_dimensions_too_small(self) -> None:
        """Test returns False when both dimensions are too small."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 10,
                lines=MIN_TERMINAL_HEIGHT - 5,
            )
            assert check_terminal_size() is False

    def test_terminal_size_exception_returns_true(self) -> None:
        """Test returns True when terminal size cannot be determined."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.side_effect = Exception("Cannot determine size")
            # Should return True and proceed anyway
            assert check_terminal_size() is True


class TestShowTerminalSizeError:
    """Test the show_terminal_size_error function."""

    def test_show_error_with_rich_console(self, capsys) -> None:
        """Test error message with Rich console."""
        mock_console = MagicMock(spec=Console)

        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 20,
                lines=MIN_TERMINAL_HEIGHT - 10,
            )

            with pytest.raises(SystemExit) as exc_info:
                show_terminal_size_error(console=mock_console, use_rich=True)

            assert exc_info.value.code == 1
            # Verify console.print was called
            assert mock_console.print.call_count >= 3

    def test_show_error_creates_console_when_none(self) -> None:
        """Test creates console when none provided."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 20,
                lines=MIN_TERMINAL_HEIGHT - 10,
            )

            with patch("pysetitup.ui.terminal_check.Console") as mock_console_cls:
                mock_console = MagicMock(spec=Console)
                mock_console_cls.return_value = mock_console

                with pytest.raises(SystemExit) as exc_info:
                    show_terminal_size_error(console=None, use_rich=True)

                assert exc_info.value.code == 1
                mock_console_cls.assert_called_once()

    def test_show_error_plain_text_output(self, capsys) -> None:
        """Test error message with plain text output."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 20,
                lines=MIN_TERMINAL_HEIGHT - 10,
            )

            with pytest.raises(SystemExit) as exc_info:
                show_terminal_size_error(console=None, use_rich=False)

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "Terminal size is too small" in captured.out
            assert f"{MIN_TERMINAL_WIDTH} columns" in captured.out
            assert f"{MIN_TERMINAL_HEIGHT} lines" in captured.out

    def test_show_error_displays_current_size(self, capsys) -> None:
        """Test error displays current terminal size."""
        current_width = MIN_TERMINAL_WIDTH - 20
        current_height = MIN_TERMINAL_HEIGHT - 10

        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=current_width,
                lines=current_height,
            )

            with pytest.raises(SystemExit):
                show_terminal_size_error(console=None, use_rich=False)

            captured = capsys.readouterr()
            assert f"Current size: {current_width} columns" in captured.out
            assert "Need 20 more columns" in captured.out
            assert "Need 10 more lines" in captured.out

    def test_show_error_when_size_cannot_be_determined(self, capsys) -> None:
        """Test error message when terminal size cannot be determined."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.side_effect = Exception("Cannot determine size")

            with pytest.raises(SystemExit) as exc_info:
                show_terminal_size_error(console=None, use_rich=False)

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            assert "Terminal size is too small" in captured.out
            # Should not display current size since it's unknown
            assert "Current size:" not in captured.out

    def test_show_error_width_only_too_small(self, capsys) -> None:
        """Test error when only width is too small."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 15,
                lines=MIN_TERMINAL_HEIGHT + 10,
            )

            with pytest.raises(SystemExit):
                show_terminal_size_error(console=None, use_rich=False)

            captured = capsys.readouterr()
            assert "Need 15 more columns" in captured.out
            assert "more lines" not in captured.out

    def test_show_error_height_only_too_small(self, capsys) -> None:
        """Test error when only height is too small."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH + 10,
                lines=MIN_TERMINAL_HEIGHT - 5,
            )

            with pytest.raises(SystemExit):
                show_terminal_size_error(console=None, use_rich=False)

            captured = capsys.readouterr()
            assert "Need 5 more lines" in captured.out
            assert "more columns" not in captured.out


class TestCheckAndEnforceTerminalSize:
    """Test the check_and_enforce_terminal_size function."""

    def test_enforce_passes_when_size_sufficient(self) -> None:
        """Test does not exit when terminal size is sufficient."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH,
                lines=MIN_TERMINAL_HEIGHT,
            )

            # Should not raise SystemExit
            check_and_enforce_terminal_size(console=None, use_rich=False)

    def test_enforce_exits_when_size_too_small(self, capsys) -> None:
        """Test exits when terminal size is too small."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 1,
                lines=MIN_TERMINAL_HEIGHT - 1,
            )

            with pytest.raises(SystemExit) as exc_info:
                check_and_enforce_terminal_size(console=None, use_rich=False)

            assert exc_info.value.code == 1

    def test_enforce_with_console_argument(self) -> None:
        """Test enforce with console argument."""
        mock_console = MagicMock(spec=Console)

        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 10,
                lines=MIN_TERMINAL_HEIGHT - 5,
            )

            with pytest.raises(SystemExit):
                check_and_enforce_terminal_size(console=mock_console, use_rich=True)

            # Verify console was used
            assert mock_console.print.call_count >= 3

    def test_enforce_plain_text_mode(self, capsys) -> None:
        """Test enforce with plain text mode."""
        with patch("shutil.get_terminal_size") as mock_size:
            mock_size.return_value = MagicMock(
                columns=MIN_TERMINAL_WIDTH - 20,
                lines=MIN_TERMINAL_HEIGHT,
            )

            with pytest.raises(SystemExit):
                check_and_enforce_terminal_size(console=None, use_rich=False)

            captured = capsys.readouterr()
            assert "Terminal size is too small" in captured.out
