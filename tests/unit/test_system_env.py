"""Unit tests for pysetitup.system.env module."""

import os
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from pysetitup.system.env import (
    check_macos_requirement,
    ensure_pysetitup_dir,
    get_home_dir,
    get_macos_version,
    get_pysetitup_dir,
    get_shell,
    is_ci,
    is_macos,
    is_tty,
)
from pysetitup.utils.errors import SystemError


class TestMacOSDetection:
    """Test macOS detection functions."""

    def test_is_macos_on_darwin(self) -> None:
        """Test is_macos returns True on Darwin."""
        with patch("platform.system", return_value="Darwin"):
            assert is_macos() is True

    def test_is_macos_on_linux(self) -> None:
        """Test is_macos returns False on Linux."""
        with patch("platform.system", return_value="Linux"):
            assert is_macos() is False

    def test_is_macos_on_windows(self) -> None:
        """Test is_macos returns False on Windows."""
        with patch("platform.system", return_value="Windows"):
            assert is_macos() is False

    def test_get_macos_version_on_macos(self) -> None:
        """Test get_macos_version returns version string on macOS."""
        with patch("platform.system", return_value="Darwin"):
            with patch("platform.mac_ver", return_value=("14.2.1", (), ())):
                version = get_macos_version()
                assert version == "14.2.1"

    def test_get_macos_version_on_non_macos(self) -> None:
        """Test get_macos_version returns None on non-macOS."""
        with patch("platform.system", return_value="Linux"):
            assert get_macos_version() is None


class TestTTYDetection:
    """Test TTY detection functions."""

    def test_is_tty_when_both_are_tty(self) -> None:
        """Test is_tty returns True when stdin and stdout are TTY."""
        with patch("sys.stdin.isatty", return_value=True):
            with patch("sys.stdout.isatty", return_value=True):
                assert is_tty() is True

    def test_is_tty_when_stdin_not_tty(self) -> None:
        """Test is_tty returns False when stdin is not TTY."""
        with patch("sys.stdin.isatty", return_value=False):
            with patch("sys.stdout.isatty", return_value=True):
                assert is_tty() is False

    def test_is_tty_when_stdout_not_tty(self) -> None:
        """Test is_tty returns False when stdout is not TTY."""
        with patch("sys.stdin.isatty", return_value=True):
            with patch("sys.stdout.isatty", return_value=False):
                assert is_tty() is False

    def test_is_tty_when_neither_is_tty(self) -> None:
        """Test is_tty returns False when neither is TTY."""
        with patch("sys.stdin.isatty", return_value=False):
            with patch("sys.stdout.isatty", return_value=False):
                assert is_tty() is False


class TestCIDetection:
    """Test CI environment detection."""

    def test_is_ci_in_github_actions(self) -> None:
        """Test is_ci detects GitHub Actions."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert is_ci() is True

    def test_is_ci_with_ci_variable(self) -> None:
        """Test is_ci detects generic CI variable."""
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            assert is_ci() is True

    def test_is_ci_in_gitlab(self) -> None:
        """Test is_ci detects GitLab CI."""
        with patch.dict(os.environ, {"GITLAB_CI": "true"}, clear=True):
            assert is_ci() is True

    def test_is_ci_not_in_ci(self) -> None:
        """Test is_ci returns False when not in CI."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_ci() is False


class TestShellDetection:
    """Test shell detection."""

    def test_get_shell_zsh(self) -> None:
        """Test get_shell detects zsh."""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            assert get_shell() == "zsh"

    def test_get_shell_bash(self) -> None:
        """Test get_shell detects bash."""
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert get_shell() == "bash"

    def test_get_shell_with_full_path(self) -> None:
        """Test get_shell extracts basename from full path."""
        with patch.dict(os.environ, {"SHELL": "/usr/local/bin/fish"}):
            assert get_shell() == "fish"

    def test_get_shell_when_not_set(self) -> None:
        """Test get_shell returns None when SHELL not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_shell() is None


class TestDirectoryFunctions:
    """Test directory-related functions."""

    def test_get_home_dir(self) -> None:
        """Test get_home_dir returns expanded home directory."""
        home = get_home_dir()
        assert home == os.path.expanduser("~")
        assert len(home) > 0
        assert not home.startswith("~")

    def test_get_pysetitup_dir(self) -> None:
        """Test get_pysetitup_dir returns ~/.pysetitup path."""
        pysetitup_dir = get_pysetitup_dir()
        assert pysetitup_dir.endswith(".pysetitup")
        assert pysetitup_dir == os.path.join(os.path.expanduser("~"), ".pysetitup")

    def test_ensure_pysetitup_dir_creates_directory(self, temp_dir: Path) -> None:
        """Test ensure_pysetitup_dir creates directory if it doesn't exist."""
        test_home = temp_dir / "test_home"

        with patch("pysetitup.system.env.get_home_dir", return_value=str(test_home)):
            pysetitup_dir = ensure_pysetitup_dir()
            assert os.path.exists(pysetitup_dir)
            assert os.path.isdir(pysetitup_dir)
            assert pysetitup_dir == str(test_home / ".pysetitup")

    def test_ensure_pysetitup_dir_idempotent(self, temp_dir: Path) -> None:
        """Test ensure_pysetitup_dir is idempotent (can be called multiple times)."""
        test_home = temp_dir / "test_home"

        with patch("pysetitup.system.env.get_home_dir", return_value=str(test_home)):
            dir1 = ensure_pysetitup_dir()
            dir2 = ensure_pysetitup_dir()
            assert dir1 == dir2
            assert os.path.exists(dir1)


class TestMacOSRequirement:
    """Test macOS requirement checking."""

    def test_check_macos_requirement_on_macos(self) -> None:
        """Test check_macos_requirement passes on macOS."""
        with patch("platform.system", return_value="Darwin"):
            # Should not raise
            check_macos_requirement()

    def test_check_macos_requirement_on_linux(self) -> None:
        """Test check_macos_requirement raises on Linux."""
        with patch("platform.system", return_value="Linux"):
            with pytest.raises(SystemError) as exc_info:
                check_macos_requirement()
            assert "PySetItUp requires macOS" in str(exc_info.value)
            assert "detected Linux" in str(exc_info.value)

    def test_check_macos_requirement_on_windows(self) -> None:
        """Test check_macos_requirement raises on Windows."""
        with patch("platform.system", return_value="Windows"):
            with pytest.raises(SystemError) as exc_info:
                check_macos_requirement()
            assert "PySetItUp requires macOS" in str(exc_info.value)
            assert "detected Windows" in str(exc_info.value)
