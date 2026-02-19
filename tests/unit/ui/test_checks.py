"""Unit tests for pysetitup.ui.checks module."""

from io import StringIO

from rich.console import Console

from pysetitup.ui.checks import (
    SystemChecks,
    check_git,
    check_git_config,
    check_homebrew,
    check_npm,
    check_ssh_key,
    check_terminal_size,
    check_vscode,
    run_system_checks,
)


class TestSystemChecks:
    """Test SystemChecks class."""

    def test_add_check(self) -> None:
        """Test adding checks."""
        checks = SystemChecks()

        checks.add_check("Test", "pass", "Test message")

        assert len(checks.checks) == 1
        assert checks.checks[0]["name"] == "Test"
        assert checks.checks[0]["status"] == "pass"

    def test_display_all_pass(self) -> None:
        """Test display when all checks pass."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        checks = SystemChecks(console)

        checks.add_check("Check 1", "pass", "Success", required=True)
        checks.add_check("Check 2", "pass", "Success", required=True)

        result = checks.display()

        assert result is True

    def test_display_required_fail(self) -> None:
        """Test display when required check fails."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        checks = SystemChecks(console)

        checks.add_check("Required", "fail", "Failed", required=True)
        checks.add_check("Optional", "pass", "Success", required=False)

        result = checks.display()

        assert result is False

    def test_display_optional_fail(self) -> None:
        """Test display when optional check fails."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        checks = SystemChecks(console)

        checks.add_check("Required", "pass", "Success", required=True)
        checks.add_check("Optional", "fail", "Failed", required=False)

        result = checks.display()

        assert result is True  # Optional fail doesn't block

    def test_clear(self) -> None:
        """Test clearing checks."""
        checks = SystemChecks()
        checks.add_check("Test", "pass")

        checks.clear()

        assert len(checks.checks) == 0


class TestCheckFunctions:
    """Test individual check functions."""

    def test_check_homebrew(self) -> None:
        """Test Homebrew check."""
        status, message = check_homebrew()

        assert status in ("pass", "fail")
        assert isinstance(message, str)
        assert len(message) > 0

    def test_check_git(self) -> None:
        """Test Git check."""
        status, message = check_git()

        assert status in ("pass", "warn")
        assert isinstance(message, str)

    def test_check_vscode(self) -> None:
        """Test VS Code CLI check."""
        status, message = check_vscode()

        assert status in ("pass", "warn")
        assert isinstance(message, str)

    def test_check_npm(self) -> None:
        """Test npm check."""
        status, message = check_npm()

        assert status in ("pass", "warn")
        assert isinstance(message, str)

    def test_check_terminal_size(self) -> None:
        """Test terminal size check."""
        status, message = check_terminal_size(min_width=10, min_height=10)

        assert status in ("pass", "fail", "skip")
        assert isinstance(message, str)

    def test_check_git_config(self) -> None:
        """Test Git configuration check."""
        status, message = check_git_config()

        assert status in ("pass", "warn", "skip")
        assert isinstance(message, str)
        assert len(message) > 0

    def test_check_ssh_key(self) -> None:
        """Test SSH key check."""
        status, message = check_ssh_key()

        assert status in ("pass", "warn")
        assert isinstance(message, str)
        assert len(message) > 0


class TestRunSystemChecks:
    """Test run_system_checks function."""

    def test_run_system_checks_no_extensions(self) -> None:
        """Test system checks without VS Code extensions."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        result = run_system_checks(vscode_extensions=[], npm_packages=[], console=console)

        assert isinstance(result, bool)

    def test_run_system_checks_with_vscode(self) -> None:
        """Test system checks with VS Code extensions."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        result = run_system_checks(vscode_extensions=["ms-python.python"], npm_packages=[], console=console)

        assert isinstance(result, bool)

    def test_run_system_checks_with_npm(self) -> None:
        """Test system checks with npm packages."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)

        result = run_system_checks(vscode_extensions=[], npm_packages=["typescript"], console=console)

        assert isinstance(result, bool)
