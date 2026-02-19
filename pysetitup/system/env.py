"""System environment detection and utilities."""

import os
import platform
import sys
from typing import Optional


def is_macos() -> bool:
    """Check if the current operating system is macOS."""
    return platform.system() == "Darwin"


def get_macos_version() -> Optional[str]:
    """
    Get the macOS version string.

    Returns:
        macOS version (e.g., "14.2.1") or None if not on macOS
    """
    if not is_macos():
        return None
    return platform.mac_ver()[0]


def is_tty() -> bool:
    """
    Check if running in a TTY (terminal).

    Returns:
        True if stdin and stdout are connected to a terminal
    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def is_ci() -> bool:
    """
    Check if running in a CI environment.

    Returns:
        True if running in CI (GitHub Actions, etc.)
    """
    ci_indicators = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "TRAVIS",
        "JENKINS_HOME",
    ]
    return any(os.getenv(key) for key in ci_indicators)


def get_shell() -> Optional[str]:
    """
    Get the current shell name.

    Returns:
        Shell name (e.g., "zsh", "bash") or None if not found
    """
    shell_path = os.getenv("SHELL")
    if not shell_path:
        return None
    return os.path.basename(shell_path)


def get_home_dir() -> str:
    """
    Get the user's home directory.

    Returns:
        Absolute path to home directory
    """
    return os.path.expanduser("~")


def get_pysetitup_dir() -> str:
    """
    Get the PySetItUp state directory.

    Returns:
        Absolute path to ~/.pysetitup
    """
    return os.path.join(get_home_dir(), ".pysetitup")


def ensure_pysetitup_dir() -> str:
    """
    Ensure the PySetItUp state directory exists.

    Returns:
        Absolute path to ~/.pysetitup
    """
    pysetitup_dir = get_pysetitup_dir()
    os.makedirs(pysetitup_dir, exist_ok=True)
    return pysetitup_dir


def check_macos_requirement() -> None:
    """
    Check if running on macOS and raise error if not.

    Raises:
        SystemError: If not running on macOS
    """
    if not is_macos():
        from pysetitup.utils.errors import SystemError

        raise SystemError(
            f"PySetItUp requires macOS, but detected {platform.system()}. "
            "This tool is specifically designed for macOS development environments."
        )
