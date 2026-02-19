"""Unit tests for pysetitup.config.loader module."""

import pytest

from pysetitup.config.loader import (
    load_config,
    load_embedded_packages,
    load_embedded_presets,
    load_external_presets,
)
from pysetitup.config.models import Config, Preset
from pysetitup.utils.errors import ConfigurationError


class TestLoadEmbeddedPresets:
    """Test loading embedded presets."""

    def test_load_embedded_presets_success(self) -> None:
        """Test load_embedded_presets returns presets dict."""
        presets = load_embedded_presets()

        assert isinstance(presets, dict)
        assert len(presets) > 0
        assert "minimal" in presets
        assert "developer" in presets
        assert "full" in presets

        # Verify they are Preset objects
        for preset in presets.values():
            assert isinstance(preset, Preset)
            assert preset.name
            assert preset.description

    def test_minimal_preset_contents(self) -> None:
        """Test minimal preset has expected structure."""
        presets = load_embedded_presets()
        minimal = presets["minimal"]

        # Just check it has the expected structure, not specific packages
        # since the minimal preset may be customized
        assert minimal.name == "minimal"
        assert minimal.description
        assert isinstance(minimal.packages, list)
        assert isinstance(minimal.casks, list)
        assert isinstance(minimal.vscode, list)

    def test_developer_preset_contents(self) -> None:
        """Test developer preset has expected packages."""
        presets = load_embedded_presets()
        developer = presets["developer"]

        assert "node" in developer.packages
        assert "docker" in developer.packages or "docker-compose" in developer.packages
        assert len(developer.npm) > 0
        assert "typescript" in developer.npm


class TestLoadEmbeddedPackages:
    """Test loading embedded packages."""

    def test_load_embedded_packages_success(self) -> None:
        """Test load_embedded_packages returns package list."""
        packages = load_embedded_packages()

        assert isinstance(packages, list)
        assert len(packages) > 0

        # Verify all have required fields
        for pkg in packages:
            assert pkg.name
            assert pkg.category
            assert pkg.type in ["formula", "cask", "npm", "vscode"]


class TestLoadConfig:
    """Test loading complete configuration."""

    def test_load_config_success(self) -> None:
        """Test load_config returns Config with presets and packages."""
        config = load_config()

        assert isinstance(config, Config)
        assert len(config.presets) >= 3
        assert len(config.packages) > 0

        # Verify config methods work
        assert config.get_preset("minimal") is not None
        categories = config.get_all_categories()
        assert len(categories) > 0


class TestLoadExternalPresets:
    """Test loading presets from external YAML files."""

    def test_load_external_presets_success(self, tmp_path) -> None:
        """Test loading valid external presets file."""
        presets_file = tmp_path / "my_presets.yaml"
        presets_file.write_text(
            """
presets:
  custom:
    name: custom
    description: My custom preset
    packages:
      - git
      - neovim
    casks:
      - iterm2
    npm:
      - prettier
    taps: []
    vscode:
      - ms-python.python
"""
        )

        presets = load_external_presets(presets_file)

        assert "custom" in presets
        assert presets["custom"].name == "custom"
        assert "git" in presets["custom"].packages
        assert "iterm2" in presets["custom"].casks
        assert "prettier" in presets["custom"].npm
        assert "ms-python.python" in presets["custom"].vscode

    def test_load_external_presets_file_not_found(self, tmp_path) -> None:
        """Test error when external presets file doesn't exist."""
        nonexistent_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigurationError) as exc_info:
            load_external_presets(nonexistent_file)

        assert "not found" in str(exc_info.value).lower()

    def test_load_external_presets_invalid_yaml(self, tmp_path) -> None:
        """Test error when external presets file has invalid YAML."""
        presets_file = tmp_path / "invalid.yaml"
        presets_file.write_text("invalid: yaml: syntax:")

        with pytest.raises(ConfigurationError):
            load_external_presets(presets_file)

    def test_load_config_with_external_presets(self, tmp_path) -> None:
        """Test load_config merges external presets with embedded ones."""
        presets_file = tmp_path / "my_presets.yaml"
        presets_file.write_text(
            """
presets:
  custom:
    name: custom
    description: Custom preset
    packages:
      - custom-package
    casks: []
    npm: []
    taps: []
    vscode: []
"""
        )

        config = load_config(external_presets_file=presets_file)

        # Should have both embedded and external presets
        assert "minimal" in config.presets  # Embedded
        assert "developer" in config.presets  # Embedded
        assert "custom" in config.presets  # External

        # External preset should be loaded correctly
        assert "custom-package" in config.presets["custom"].packages

    def test_load_config_external_overrides_embedded(self, tmp_path) -> None:
        """Test that external presets override embedded ones with same name."""
        presets_file = tmp_path / "override.yaml"
        presets_file.write_text(
            """
presets:
  minimal:
    name: minimal
    description: Overridden minimal
    packages:
      - overridden-package
    casks: []
    npm: []
    taps: []
    vscode: []
"""
        )

        config = load_config(external_presets_file=presets_file)

        # Minimal preset should be the external one
        minimal = config.presets["minimal"]
        assert minimal.description == "Overridden minimal"
        assert "overridden-package" in minimal.packages
