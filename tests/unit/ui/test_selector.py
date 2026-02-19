"""Unit tests for pysetitup.ui.selector module."""


from pysetitup.config.loader import load_config
from pysetitup.ui.selector import PackageSelector


class TestPackageSelector:
    """Test the PackageSelector TUI."""

    def test_bindings_are_configured(self) -> None:
        """Test that all expected key bindings are configured."""
        app = PackageSelector()

        # Get all binding keys
        binding_keys = {b.key for b in app.BINDINGS}

        # Verify essential bindings exist
        assert "space" in binding_keys
        assert "left" in binding_keys
        assert "right" in binding_keys
        assert "/" in binding_keys
        assert "enter" in binding_keys
        assert "q" in binding_keys
        assert "escape" in binding_keys

    def test_arrow_bindings_visible(self) -> None:
        """Test that arrow key bindings are visible in footer."""
        app = PackageSelector()

        # Find left and right arrow bindings
        left_binding = next(b for b in app.BINDINGS if b.key == "left")
        right_binding = next(b for b in app.BINDINGS if b.key == "right")

        # Verify they are shown in footer
        assert left_binding.show is True
        assert right_binding.show is True

        # Verify they have arrow symbols
        assert "←" in left_binding.description
        assert "→" in right_binding.description

    def test_all_visible_bindings_fit_in_footer(self) -> None:
        """Test that visible bindings are compact enough to fit in footer."""
        app = PackageSelector()

        # Get all visible bindings
        visible_bindings = [b for b in app.BINDINGS if b.show]

        # Calculate approximate footer width needed
        # Format: "key description  key description  ..."
        footer_text = "  ".join(f"{b.key} {b.description}" for b in visible_bindings)

        # Standard terminal is 80 characters wide
        # Footer should fit comfortably (with some margin for styling)
        assert len(footer_text) < 100, f"Footer text too long ({len(footer_text)} chars): {footer_text}"

    def test_bindings_have_compact_descriptions(self) -> None:
        """Test that binding descriptions are concise."""
        app = PackageSelector()

        for binding in app.BINDINGS:
            if binding.show:
                # Visible bindings should have short descriptions
                assert len(binding.description) <= 10, (
                    f"Binding '{binding.key}' description too long: "
                    f"'{binding.description}' ({len(binding.description)} chars)"
                )

    def test_arrow_bindings_order(self) -> None:
        """Test that arrow bindings appear early in the binding list."""
        app = PackageSelector()

        # Get visible binding keys in order
        visible_keys = [b.key for b in app.BINDINGS if b.show]

        # Arrow keys should appear near the beginning for visibility
        left_index = visible_keys.index("left")
        right_index = visible_keys.index("right")

        # Should be in first 5 bindings
        assert left_index < 5, f"Left arrow at position {left_index}, should be earlier"
        assert right_index < 5, f"Right arrow at position {right_index}, should be earlier"

        # Should be adjacent to each other
        assert abs(left_index - right_index) == 1, "Left and right arrows should be next to each other"

    def test_selector_initializes_with_config(self) -> None:
        """Test PackageSelector can initialize with config."""
        config = load_config()
        app = PackageSelector(config=config)

        assert app.config is not None
        assert len(app.categories) > 0
        assert app.categories[0] == "All"

    def test_selector_initializes_with_preset_packages(self) -> None:
        """Test PackageSelector can initialize with preset packages."""
        config = load_config()
        preset = config.get_preset("minimal")
        initial_packages = set(preset.packages) if preset else set()

        app = PackageSelector(config=config, preset_packages=initial_packages)

        assert app.selected_packages == initial_packages

    def test_categories_include_all(self) -> None:
        """Test that categories list includes 'All' as first item."""
        app = PackageSelector()

        assert len(app.categories) > 0
        assert app.categories[0] == "All"

    def test_package_map_initialized_empty(self) -> None:
        """Test that package_map starts empty."""
        app = PackageSelector()

        assert isinstance(app.package_map, dict)
        assert len(app.package_map) == 0

    def test_search_active_starts_false(self) -> None:
        """Test that search mode starts inactive."""
        app = PackageSelector()

        assert app.search_active is False

    def test_current_category_starts_all(self) -> None:
        """Test that current category starts as 'All'."""
        app = PackageSelector()

        assert app.current_category == "All"

    def test_bindings_action_names(self) -> None:
        """Test that binding actions are correctly named."""
        app = PackageSelector()

        # Get binding action names
        actions = {b.action for b in app.BINDINGS}

        # Verify expected actions exist
        assert "toggle_package" in actions
        assert "prev_category" in actions
        assert "next_category" in actions
        assert "search" in actions
        assert "confirm" in actions
        assert "quit" in actions
        assert "clear_search" in actions

    def test_installed_packages_cache_initializes_empty(self) -> None:
        """Test that installed packages cache starts empty."""
        app = PackageSelector()

        assert isinstance(app.installed_packages, dict)
        assert len(app.installed_packages) == 0

    def test_get_installed_status_not_installed(self) -> None:
        """Test installed status for package not in cache."""
        app = PackageSelector()

        status = app._get_installed_status("nonexistent-package")

        assert status == "-"

    def test_get_installed_status_installed_no_version(self) -> None:
        """Test installed status for package without version."""
        app = PackageSelector()
        app.installed_packages["git"] = None

        status = app._get_installed_status("git")

        assert status == "✓"

    def test_get_installed_status_installed_with_version(self) -> None:
        """Test installed status for package with version."""
        app = PackageSelector()
        app.installed_packages["typescript"] = "5.0.0"

        status = app._get_installed_status("typescript")

        assert status == "✓ 5.0.0"
