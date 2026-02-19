"""Unit tests for pysetitup.ui.confirmation module."""

from pysetitup.ui.confirmation import ConfirmationScreen


class TestConfirmationScreen:
    """Test the ConfirmationScreen TUI."""

    def test_initialization(self) -> None:
        """Test ConfirmationScreen initializes correctly."""
        packages = ["git", "fzf", "ripgrep"]
        installed = {"git": "2.43.0"}

        app = ConfirmationScreen(packages, installed)

        assert app.packages == packages
        assert app.installed_packages == installed
        assert app.confirmed is False

    def test_initialization_empty_installed(self) -> None:
        """Test ConfirmationScreen with no installed packages."""
        packages = ["git", "fzf"]
        installed = {}

        app = ConfirmationScreen(packages, installed)

        assert app.packages == packages
        assert app.installed_packages == {}
        assert app.confirmed is False

    def test_bindings_configured(self) -> None:
        """Test that confirmation bindings are configured."""
        app = ConfirmationScreen(["git"], {})

        binding_keys = {b.key for b in app.BINDINGS}

        assert "y" in binding_keys
        assert "n" in binding_keys
        assert "q" in binding_keys

    def test_bindings_visible(self) -> None:
        """Test that bindings are visible in footer."""
        app = ConfirmationScreen(["git"], {})

        visible_bindings = [b for b in app.BINDINGS if b.show]

        assert len(visible_bindings) >= 2
        assert any(b.key == "y" for b in visible_bindings)
        assert any(b.key == "n" for b in visible_bindings)

    def test_bindings_have_priority(self) -> None:
        """Test that bindings have priority set."""
        app = ConfirmationScreen(["git"], {})

        for binding in app.BINDINGS:
            if binding.show:
                assert binding.priority is True
