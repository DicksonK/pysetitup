"""Confirmation screen for package installation."""

from collections.abc import Awaitable, Callable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Label, Static


class PackageList(Static):
    """Widget to display the list of packages to install."""

    DEFAULT_CSS = """
    PackageList {
        height: auto;
        padding: 1 2;
        background: $panel;
        border: solid $accent;
        margin: 1 0;
    }

    .package-item {
        padding: 0 1;
    }

    .already-installed {
        color: $success;
    }

    .to-install {
        color: $text;
    }
    """


class ConfirmationScreen(App):
    """Confirmation screen before installing packages."""

    TITLE = "Installation Confirmation"
    SUB_TITLE = "Review your selections before installing"

    CSS = """
    Screen {
        background: $surface;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
    }

    #summary {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    #instructions {
        text-align: center;
        padding: 1;
        color: $warning;
        text-style: bold;
    }

    #package-container {
        height: auto;
        max-height: 70%;
        padding: 0 4;
    }

    #package-scroll {
        height: auto;
        max-height: 100%;
    }
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes, Install", show=True, priority=True),
        Binding("n", "cancel", "No, Cancel", show=True, priority=True),
        Binding("q", "cancel", "Quit", show=True, priority=True),
    ]

    def __init__(
        self,
        packages: list[str],
        installed_packages: dict[str, str | None] | None = None,
        get_installed_packages_func: Callable[[], Awaitable[dict[str, str | None]]] | None = None,
    ):
        """
        Initialize confirmation screen.

        Args:
            packages: List of package names to install
            installed_packages: Dict of already installed packages with versions (if already known)
            get_installed_packages_func: Async function to get installed packages (if not yet known)
        """
        super().__init__()
        self.packages = packages
        self.installed_packages = installed_packages or {}
        self.get_installed_packages_func = get_installed_packages_func
        self.confirmed = False
        # Always check packages if we have a function, regardless of initial state
        self.checking_packages = get_installed_packages_func is not None

    def compose(self) -> ComposeResult:
        """Compose the confirmation screen layout."""
        yield Header()

        yield Label("Package Installation Confirmation", id="title")

        # Summary label (will be updated after checking)
        if self.checking_packages:
            summary = f"Total: {len(self.packages)} packages  |  Checking installed packages..."
        else:
            already_installed = [p for p in self.packages if p in self.installed_packages]
            to_install = [p for p in self.packages if p not in self.installed_packages]
            summary = (
                f"Total: {len(self.packages)} packages  |  "
                f"Already installed: {len(already_installed)}  |  "
                f"To install: {len(to_install)}"
            )
        yield Label(summary, id="summary")

        # Create scrollable container for packages
        with Container(id="package-container"):
            with VerticalScroll(id="package-scroll"):
                if self.checking_packages:
                    yield Label("\n[dim]🔍 Checking which packages are already installed...[/dim]")
                    yield Label("[dim]This may take a moment...[/dim]")
                else:
                    already_installed = [p for p in self.packages if p in self.installed_packages]
                    to_install = [p for p in self.packages if p not in self.installed_packages]

                    if to_install:
                        yield Label("\n[bold]Packages to install:[/bold]")
                        for pkg in sorted(to_install):
                            yield Label(f"  • {pkg}", classes="package-item to-install")

                    if already_installed:
                        yield Label("\n[bold]Already installed (will be skipped):[/bold]")
                        for pkg in sorted(already_installed):
                            version = self.installed_packages.get(pkg)
                            version_str = f" ({version})" if version else ""
                            yield Label(
                                f"  ✓ {pkg}{version_str}",
                                classes="package-item already-installed",
                            )

        yield Label("\nProceed with installation?", id="instructions")

        yield Footer()

    def on_mount(self) -> None:
        """Set focus to the scroll container after mounting and check packages if needed."""
        scroll = self.query_one("#package-scroll", VerticalScroll)
        scroll.focus()

        # Start checking packages if needed
        if self.checking_packages and self.get_installed_packages_func:
            self.run_worker(self._check_packages(), exclusive=True)

    async def _check_packages(self) -> None:
        """Check which packages are already installed."""
        if self.get_installed_packages_func:
            self.installed_packages = await self.get_installed_packages_func()
            self.checking_packages = False
            self._update_display()

    def _update_display(self) -> None:
        """Update the summary and package list after checking installed packages."""
        # Update summary
        already_installed = [p for p in self.packages if p in self.installed_packages]
        to_install = [p for p in self.packages if p not in self.installed_packages]

        summary = (
            f"Total: {len(self.packages)} packages  |  "
            f"Already installed: {len(already_installed)}  |  "
            f"To install: {len(to_install)}"
        )
        summary_label = self.query_one("#summary", Label)
        summary_label.update(summary)

        # Update package list
        scroll = self.query_one("#package-scroll", VerticalScroll)
        scroll.remove_children()

        if to_install:
            scroll.mount(Label("\n[bold]Packages to install:[/bold]"))
            for pkg in sorted(to_install):
                scroll.mount(Label(f"  • {pkg}", classes="package-item to-install"))

        if already_installed:
            scroll.mount(Label("\n[bold]Already installed (will be skipped):[/bold]"))
            for pkg in sorted(already_installed):
                version = self.installed_packages.get(pkg)
                version_str = f" ({version})" if version else ""
                scroll.mount(
                    Label(
                        f"  ✓ {pkg}{version_str}",
                        classes="package-item already-installed",
                    )
                )

    def action_confirm(self) -> None:
        """User confirmed - proceed with installation."""
        self.confirmed = True
        self.exit(True)

    def action_cancel(self) -> None:
        """User cancelled - exit without installing."""
        self.confirmed = False
        self.exit(False)


async def show_confirmation(
    packages: list[str],
    installed_packages: dict[str, str | None] | None = None,
    get_installed_packages_func: Callable[[], Awaitable[dict[str, str | None]]] | None = None,
) -> bool:
    """
    Show confirmation screen and get user approval.

    Args:
        packages: List of package names to install
        installed_packages: Dict of already installed packages with versions (if already known)
        get_installed_packages_func: Async function to get installed packages (if not yet known)

    Returns:
        True if user confirmed, False if cancelled
    """
    app = ConfirmationScreen(packages, installed_packages, get_installed_packages_func)
    result = await app.run_async()
    return bool(result)
