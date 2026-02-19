"""Interactive preset selector TUI using Textual."""

from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Footer, Header, Label, Static

from pysetitup.config.loader import load_config
from pysetitup.config.models import Config, Preset


class PresetCard(Static):
    """A card displaying preset information."""

    DEFAULT_CSS = """
    PresetCard {
        width: 1fr;
        height: 12;
        padding: 1;
        margin: 0 1;
        border: solid $accent;
        background: $panel;
        overflow: hidden;
    }

    PresetCard:hover {
        border: solid $success;
        background: $panel-lighten-1;
    }

    PresetCard.selected {
        border: double $success;
        background: $success 20%;
    }

    PresetCard:focus {
        border: double $success;
        background: $success 20%;
    }

    .preset-name {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
        width: 100%;
    }

    .preset-description {
        color: $text;
        padding-bottom: 1;
        width: 100%;
        text-wrap: wrap;
    }

    .preset-stats {
        color: $text-muted;
        width: 100%;
        text-wrap: wrap;
    }
    """

    class Selected(Message):
        """Message sent when a preset card is clicked."""

        def __init__(self, preset_name: str) -> None:
            super().__init__()
            self.preset_name = preset_name

    def __init__(self, preset: Preset, selected: bool = False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.preset = preset
        self.is_selected = selected
        if selected:
            self.add_class("selected")
        # Make the card focusable and clickable
        self.can_focus = True

    def compose(self) -> ComposeResult:
        """Compose the preset card layout."""
        # Count packages
        cli_count = len(self.preset.packages)
        cask_count = len(self.preset.casks)
        npm_count = len(self.preset.npm)
        vscode_count = len(self.preset.vscode)
        total = cli_count + cask_count + npm_count + vscode_count

        stats_parts = []
        if cli_count > 0:
            stats_parts.append(f"{cli_count} CLI")
        if cask_count > 0:
            stats_parts.append(f"{cask_count} apps")
        if npm_count > 0:
            stats_parts.append(f"{npm_count} npm")
        if vscode_count > 0:
            stats_parts.append(f"{vscode_count} VSCode")

        stats = f"{total} packages total: " + ", ".join(stats_parts) if stats_parts else "No packages"

        yield Label(f"📦 {self.preset.name.upper()}", classes="preset-name")
        yield Label(self.preset.description, classes="preset-description")
        yield Label(stats, classes="preset-stats")

    def on_click(self) -> None:
        """Handle click on the preset card."""
        self.post_message(self.Selected(self.preset.name))


class PresetSelector(App):
    """Interactive TUI for selecting a preset."""

    TITLE = "Preset Selector"
    SUB_TITLE = "Choose your Mac development environment setup"

    CSS = """
    Screen {
        background: $surface;
        overflow: hidden;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
        height: 3;
    }

    #subtitle {
        text-align: center;
        color: $text-muted;
        padding: 0 2 1 2;
        height: 3;
    }

    #preset-container {
        height: auto;
        padding: 0 4;
        overflow: hidden;
    }

    Horizontal {
        overflow: hidden;
        height: auto;
    }

    #button-container {
        height: auto;
        padding: 1 4;
        align: center middle;
    }

    #button-container Horizontal {
        align: center middle;
    }

    Button {
        width: 1fr;
        min-height: 5;
        height: auto;
        margin: 0 1;
        content-align: center middle;
    }

    #install-direct {
        background: $success;
    }

    #install-direct:hover {
        background: $success-darken-1;
    }

    #customize {
        background: $accent;
    }

    #customize:hover {
        background: $accent-darken-1;
    }

    #skip {
        background: $panel;
    }

    #skip:hover {
        background: $panel-lighten-1;
    }
    """

    BINDINGS = [
        Binding("left", "navigate_left", "←", show=True, priority=True),
        Binding("right", "navigate_right", "→", show=True, priority=True),
        Binding("enter", "install_direct", "Install", show=True, priority=True),
        Binding("c", "customize", "Customize", show=True, priority=True),
        Binding("s", "skip", "Skip", show=True, priority=True),
        Binding("q", "quit", "Quit", show=True, priority=True),
    ]

    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or load_config()
        self.selected_preset: Optional[str] = None
        self.preset_cards: dict[str, PresetCard] = {}
        self.preset_order = ["minimal", "developer", "full"]
        # Disable scrolling
        self.can_scroll = False

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()

        yield Label("Select a Preset", id="title")
        yield Label(
            "Choose a preset to get started quickly, or skip to select individual packages",
            id="subtitle"
        )

        with Container(id="preset-container"):
            with Horizontal():
                # Get presets - display side by side
                presets = ["minimal", "developer", "full"]
                for preset_name in presets:
                    preset = self.config.get_preset(preset_name)
                    if preset:
                        card = PresetCard(preset, selected=(preset_name == "developer"))
                        card.id = f"preset-{preset_name}"
                        self.preset_cards[preset_name] = card
                        yield card

        # Set default selection
        if not self.selected_preset:
            self.selected_preset = "developer"

        with Container(id="button-container"):
            with Horizontal():
                yield Button("✓ Install Preset Directly", id="install-direct", variant="success")
                yield Button("✏ Customize Package Selection", id="customize", variant="primary")
                yield Button("→ Skip (Select Individual Packages)", id="skip")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the default selection and focus."""
        # Focus the first button
        self.query_one("#install-direct", Button).focus()

    def on_preset_card_selected(self, message: PresetCard.Selected) -> None:
        """Handle preset card selection via click."""
        self._select_preset(message.preset_name)

    def _select_preset(self, preset_name: str) -> None:
        """Select a preset and update UI."""
        # Remove selection from all cards
        for card in self.preset_cards.values():
            card.remove_class("selected")

        # Add selection to the clicked card
        if preset_name in self.preset_cards:
            selected_card = self.preset_cards[preset_name]
            selected_card.add_class("selected")
            self.selected_preset = preset_name

    def action_navigate_left(self) -> None:
        """Navigate to the previous preset (left)."""
        if not self.selected_preset:
            self.selected_preset = "developer"
            return

        current_index = self.preset_order.index(self.selected_preset)
        if current_index > 0:
            new_preset = self.preset_order[current_index - 1]
            self._select_preset(new_preset)

    def action_navigate_right(self) -> None:
        """Navigate to the next preset (right)."""
        if not self.selected_preset:
            self.selected_preset = "developer"
            return

        current_index = self.preset_order.index(self.selected_preset)
        if current_index < len(self.preset_order) - 1:
            new_preset = self.preset_order[current_index + 1]
            self._select_preset(new_preset)

    def action_install_direct(self) -> None:
        """Install selected preset directly without customization."""
        if self.selected_preset:
            self.exit({"action": "install", "preset": self.selected_preset})
        else:
            self.exit({"action": "skip"})

    def action_customize(self) -> None:
        """Customize package selection for the preset."""
        if self.selected_preset:
            self.exit({"action": "customize", "preset": self.selected_preset})
        else:
            self.exit({"action": "skip"})

    def action_skip(self) -> None:
        """Skip preset selection and go to individual package selection."""
        self.exit({"action": "skip"})

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "install-direct":
            self.action_install_direct()
        elif event.button.id == "customize":
            self.action_customize()
        elif event.button.id == "skip":
            self.action_skip()


async def select_preset(config: Optional[Config] = None) -> Optional[dict]:
    """
    Run the interactive preset selector TUI.

    Args:
        config: Optional Config object (will load if not provided)

    Returns:
        Dictionary with action and preset, or None if quit:
        - {"action": "install", "preset": "developer"} - Install preset directly
        - {"action": "customize", "preset": "minimal"} - Customize preset packages
        - {"action": "skip"} - Skip to individual package selection
        - None - User quit
    """
    app = PresetSelector(config=config)
    result = await app.run_async()
    return result


if __name__ == "__main__":
    # Demo: run preset selector
    import asyncio

    async def main():
        result = await select_preset()
        if result:
            print(f"\n✅ User selection: {result}")
        else:
            print("\n❌ User quit")

    asyncio.run(main())
