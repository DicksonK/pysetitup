"""Interactive package selector TUI using Textual DataTable."""

import asyncio
from typing import Optional

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, Label, Static
from thefuzz import fuzz

from pysetitup.brew.client import BrewClient
from pysetitup.config.loader import load_config
from pysetitup.config.models import Config, Package
from pysetitup.npm.client import NpmClient
from pysetitup.vscode.client import VSCodeClient


class CategoryTab(Static):
    """A category tab button."""

    DEFAULT_CSS = """
    CategoryTab {
        width: auto;
        height: 1;
        padding: 0 2;
        color: #6c7086;
    }

    CategoryTab.active {
        color: #a6e3a1;
        text-style: bold underline;
    }
    """

    def __init__(self, category: str, active: bool = False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.category = category
        self.update(category)
        if active:
            self.add_class("active")


class PackageSelector(App):
    """Interactive TUI for selecting packages."""

    TITLE = "Package Selector"
    SUB_TITLE = "Customize your package selection"

    CSS = """
    Screen {
        background: $surface;
    }

    #tabs {
        height: 3;
        background: $panel;
        padding: 1;
    }

    #search-container {
        height: 3;
        background: $panel;
        padding: 0 1;
        display: none;
    }

    #search-container.visible {
        display: block;
    }

    Input {
        width: 100%;
        border: tall $primary;
    }

    DataTable {
        height: 1fr;
    }

    DataTable > .datatable--cursor {
        background: $accent 30%;
    }

    #footer-info {
        height: 3;
        background: $panel;
        padding: 1;
    }

    .selected-count {
        color: $success;
    }

    .help-text {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("space", "toggle_package", "Select", show=True, priority=True),
        Binding("left", "prev_category", "←Cat", show=True, priority=True),
        Binding("right", "next_category", "Cat→", show=True, priority=True),
        Binding("/", "search", "Search", show=True, priority=True),
        Binding("escape", "clear_search", "ESC", show=True, priority=True),
        Binding("enter", "confirm", "Confirm", show=True, priority=True),
        Binding("q", "quit", "Quit", show=True, priority=True),
    ]

    # Reactive attributes
    current_category: reactive[str] = reactive("All")
    selected_packages: reactive[set[str]] = reactive(set, init=False)
    search_query: reactive[str] = reactive("")

    def __init__(
        self,
        config: Optional[Config] = None,
        preset_packages: Optional[set[str]] = None,
    ):
        super().__init__()
        self.config = config or load_config()
        self.selected_packages = preset_packages or set()
        self.categories = ["All"] + self.config.get_all_categories()
        self.current_category_index = 0
        self.package_map: dict[int, Package] = {}  # Row index -> Package
        self.search_active = False

        # Installation status cache: package_name -> version or None
        self.installed_packages: dict[str, Optional[str]] = {}
        self.brew_client: Optional[BrewClient] = None
        self.npm_client: Optional[NpmClient] = None
        self.vscode_client: Optional[VSCodeClient] = None

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()

        # Category tabs
        with Horizontal(id="tabs"):
            for i, category in enumerate(self.categories):
                yield CategoryTab(category, active=(i == 0))

        # Search bar (hidden by default)
        with Container(id="search-container"):
            yield Input(placeholder="Type to search...", id="search-input")

        # Package table
        table = DataTable(cursor_type="row", zebra_stripes=True)
        table.add_columns("☐", "Package", "Type", "Installed", "Description")
        yield table

        # Footer info
        with Container(id="footer-info"):
            yield Label("", id="selected-count", classes="selected-count")
            yield Label(
                "[Space] Toggle  [←/→] Category  [/] Search  [Enter] Confirm  [q] Quit",
                classes="help-text",
            )

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the package table when app mounts."""
        self._update_table()
        self._update_footer()
        # Focus the table by default
        self.query_one(DataTable).focus()
        # Load installed packages in background
        self._load_installed_packages()

    def _update_footer(self) -> None:
        """Update the footer with selection count."""
        count = len(self.selected_packages)
        label = self.query_one("#selected-count", Label)
        label.update(f"[b]Selected:[/b] [green]{count}[/green] packages")

    def _get_filtered_packages(self) -> list[Package]:
        """Get packages filtered by category and search query."""
        packages = self.config.packages

        # Filter by category
        if self.current_category != "All":
            packages = [p for p in packages if p.category == self.current_category]

        # Filter by search query
        if self.search_query:
            query_lower = self.search_query.lower()
            filtered = []

            for pkg in packages:
                pkg_name_lower = pkg.name.lower()
                desc = (pkg.description or "").lower()

                # 1. Exact substring match in name (highest priority)
                if query_lower in pkg_name_lower:
                    filtered.append((pkg, 100))  # Score: 100
                # 2. Name starts with query (high priority)
                elif pkg_name_lower.startswith(query_lower):
                    filtered.append((pkg, 90))  # Score: 90
                # 3. Fuzzy match on name (medium priority)
                else:
                    name_score = fuzz.ratio(query_lower, pkg_name_lower)
                    desc_score = fuzz.partial_ratio(query_lower, desc)

                    # Higher threshold for better matches
                    if name_score > 70:
                        filtered.append((pkg, name_score))
                    elif desc_score > 75:
                        filtered.append((pkg, desc_score - 10))  # Lower priority than name

            # Sort by score (descending), then by name
            filtered.sort(key=lambda x: (-x[1], x[0].name.lower()))
            packages = [pkg for pkg, score in filtered]
        else:
            # Only sort by type and name when NOT searching
            # This preserves relevance ordering during search
            packages = sorted(packages, key=lambda p: (p.type.lower(), p.name.lower()))

        return packages

    def _update_table(self) -> None:
        """Update the package table based on filters."""
        table = self.query_one(DataTable)
        table.clear()
        self.package_map.clear()

        packages = self._get_filtered_packages()

        for i, pkg in enumerate(packages):
            checkbox = "✓" if pkg.name in self.selected_packages else " "

            # Get installation status
            installed_status = self._get_installed_status(pkg.name)

            desc = pkg.description or ""
            if len(desc) > 40:  # Shorter to make room for Installed column
                desc = desc[:37] + "..."

            table.add_row(checkbox, pkg.name, pkg.type, installed_status, desc)
            self.package_map[i] = pkg

    def _update_category_tabs(self) -> None:
        """Update category tab highlighting."""
        tabs = self.query(CategoryTab)
        for i, tab in enumerate(tabs):
            if i == self.current_category_index:
                tab.add_class("active")
            else:
                tab.remove_class("active")

    def action_toggle_package(self) -> None:
        """Toggle the currently selected package."""
        table = self.query_one(DataTable)
        row_index = table.cursor_row

        if row_index is None or row_index not in self.package_map:
            return

        pkg = self.package_map[row_index]

        if pkg.name in self.selected_packages:
            self.selected_packages.remove(pkg.name)
        else:
            self.selected_packages.add(pkg.name)

        # Update the checkbox in the table
        checkbox = "✓" if pkg.name in self.selected_packages else " "
        table.update_cell_at((row_index, 0), checkbox)

        self._update_footer()

    def action_next_category(self) -> None:
        """Switch to next category."""
        self.current_category_index = (self.current_category_index + 1) % len(
            self.categories
        )
        self.current_category = self.categories[self.current_category_index]
        self._update_category_tabs()
        self._update_table()

    def action_prev_category(self) -> None:
        """Switch to previous category."""
        self.current_category_index = (self.current_category_index - 1) % len(
            self.categories
        )
        self.current_category = self.categories[self.current_category_index]
        self._update_category_tabs()
        self._update_table()

    def action_search(self) -> None:
        """Activate search mode."""
        self.search_active = True
        search_container = self.query_one("#search-container")
        search_container.add_class("visible")
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self) -> None:
        """Clear search and return to normal mode."""
        self.search_active = False
        self.search_query = ""
        search_container = self.query_one("#search-container")
        search_container.remove_class("visible")
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self._update_table()
        # Return focus to table
        self.query_one(DataTable).focus()

    @on(Input.Changed)
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.search_query = event.value
            self._update_table()

    def on_key(self, event) -> None:
        """Handle key events to prevent tab navigation when searching."""
        if self.search_active and event.key == "tab":
            # Prevent tab from changing focus when search is active
            event.prevent_default()
            event.stop()

    def action_confirm(self) -> None:
        """Confirm selection and exit."""
        self.exit(list(self.selected_packages))

    def action_quit(self) -> None:
        """Quit without saving."""
        self.exit([])

    def _get_installed_status(self, package_name: str) -> str:
        """Get installation status display for a package."""
        if package_name in self.installed_packages:
            version = self.installed_packages[package_name]
            if version:
                return f"✓ {version}"
            else:
                return "✓"
        return "-"

    @work(exclusive=True, thread=True)
    def _load_installed_packages(self) -> None:
        """Load installed packages in background thread."""
        try:
            # Initialize clients if needed
            if self.brew_client is None:
                try:
                    self.brew_client = BrewClient()
                except Exception:
                    pass  # Brew not available

            if self.npm_client is None:
                try:
                    self.npm_client = NpmClient()
                except Exception:
                    pass  # npm not available

            if self.vscode_client is None:
                try:
                    self.vscode_client = VSCodeClient()
                except Exception:
                    pass  # VSCode not available

            # Run async tasks in thread
            asyncio.run(self._fetch_installed_packages())

        except Exception:
            pass  # Silently fail if we can't check installed packages

    async def _fetch_installed_packages(self) -> None:
        """Fetch installed packages from brew, npm, and VSCode."""
        tasks = []

        # Fetch brew formulae
        if self.brew_client:
            tasks.append(self._fetch_brew_formulae())

        # Fetch brew casks
        if self.brew_client:
            tasks.append(self._fetch_brew_casks())

        # Fetch npm packages
        if self.npm_client:
            tasks.append(self._fetch_npm_packages())

        # Fetch VSCode extensions
        if self.vscode_client:
            tasks.append(self._fetch_vscode_extensions())

        # Wait for all fetches to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Refresh the table display
        self.call_from_thread(self._update_table)

    async def _fetch_brew_formulae(self) -> None:
        """Fetch installed Homebrew formulae with versions."""
        try:
            versions = await self.brew_client.list_formulae_versions()
            self.installed_packages.update(versions)
        except Exception:
            pass

    async def _fetch_brew_casks(self) -> None:
        """Fetch installed Homebrew casks with versions."""
        try:
            versions = await self.brew_client.list_casks_versions()
            self.installed_packages.update(versions)
        except Exception:
            pass

    async def _fetch_npm_packages(self) -> None:
        """Fetch installed npm packages with versions."""
        try:
            versions = await self.npm_client.list_global_versions()
            self.installed_packages.update(versions)
        except Exception:
            pass

    async def _fetch_vscode_extensions(self) -> None:
        """Fetch installed VSCode extensions with versions."""
        try:
            versions = await self.vscode_client.list_extensions_with_versions()
            self.installed_packages.update(versions)
        except Exception:
            pass


async def select_packages(
    config: Optional[Config] = None,
    preset_packages: Optional[set[str]] = None,
) -> list[str]:
    """
    Run the interactive package selector TUI.

    Args:
        config: Optional Config object (will load if not provided)
        preset_packages: Optional set of pre-selected packages

    Returns:
        List of selected package names
    """
    app = PackageSelector(config=config, preset_packages=preset_packages)
    result = await app.run_async()
    return result if result else []


if __name__ == "__main__":
    # Demo: run selector with minimal preset
    import asyncio

    config = load_config()
    preset = config.get_preset("minimal")
    initial_selection = set(preset.packages) if preset else set()

    selected = asyncio.run(select_packages(config, initial_selection))
    print(f"\nSelected {len(selected)} packages:")
    for pkg in selected:
        print(f"  - {pkg}")
