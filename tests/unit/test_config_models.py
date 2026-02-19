"""Unit tests for pysetitup.config.models module."""

import pytest
from pydantic import ValidationError

from pysetitup.config.models import Config, DotfilesConfig, Package, Preset


class TestPackage:
    """Test the Package model."""

    def test_package_basic(self) -> None:
        """Test Package with basic fields."""
        pkg = Package(name="git", category="CLI Tools", type="formula")
        assert pkg.name == "git"
        assert pkg.category == "CLI Tools"
        assert pkg.type == "formula"
        assert pkg.description is None
        assert pkg.tap is None

    def test_package_with_description(self) -> None:
        """Test Package with description."""
        pkg = Package(
            name="git",
            category="CLI Tools",
            type="formula",
            description="Distributed version control",
        )
        assert pkg.description == "Distributed version control"

    def test_package_with_tap(self) -> None:
        """Test Package with custom tap."""
        pkg = Package(
            name="custom-tool",
            category="Development",
            type="formula",
            tap="custom/tap",
        )
        assert pkg.tap == "custom/tap"

    def test_package_validates_type(self) -> None:
        """Test Package validates type field."""
        with pytest.raises(ValidationError):
            Package(name="test", category="Test", type="invalid")  # type: ignore


class TestPreset:
    """Test the Preset model."""

    def test_preset_basic(self) -> None:
        """Test Preset with basic fields."""
        preset = Preset(name="minimal", description="Minimal setup")
        assert preset.name == "minimal"
        assert preset.description == "Minimal setup"
        assert preset.packages == []
        assert preset.casks == []
        assert preset.npm == []
        assert preset.taps == []

    def test_preset_with_packages(self) -> None:
        """Test Preset with packages."""
        preset = Preset(
            name="developer",
            description="Developer setup",
            packages=["git", "node"],
            casks=["vscode"],
            npm=["typescript"],
            taps=["homebrew/cask"],
        )
        assert preset.packages == ["git", "node"]
        assert preset.casks == ["vscode"]
        assert preset.npm == ["typescript"]
        assert preset.taps == ["homebrew/cask"]


class TestDotfilesConfig:
    """Test the DotfilesConfig model."""

    def test_dotfiles_basic(self) -> None:
        """Test DotfilesConfig with repo."""
        config = DotfilesConfig(repo="https://github.com/user/dotfiles")
        assert config.repo == "https://github.com/user/dotfiles"
        assert config.branch is None
        assert config.stow_dirs == []

    def test_dotfiles_with_branch(self) -> None:
        """Test DotfilesConfig with branch."""
        config = DotfilesConfig(
            repo="https://github.com/user/dotfiles",
            branch="main",
            stow_dirs=["nvim", "zsh"],
        )
        assert config.branch == "main"
        assert config.stow_dirs == ["nvim", "zsh"]


class TestConfig:
    """Test the Config model."""

    def test_config_empty(self) -> None:
        """Test Config with no presets or packages."""
        config = Config()
        assert config.presets == {}
        assert config.packages == []

    def test_config_with_data(self) -> None:
        """Test Config with presets and packages."""
        preset = Preset(name="minimal", description="Minimal", packages=["git"])
        package = Package(name="git", category="CLI", type="formula")

        config = Config(presets={"minimal": preset}, packages=[package])

        assert len(config.presets) == 1
        assert "minimal" in config.presets
        assert len(config.packages) == 1

    def test_get_preset_found(self) -> None:
        """Test get_preset returns preset when found."""
        preset = Preset(name="minimal", description="Minimal")
        config = Config(presets={"minimal": preset})

        result = config.get_preset("minimal")
        assert result is not None
        assert result.name == "minimal"

    def test_get_preset_not_found(self) -> None:
        """Test get_preset returns None when not found."""
        config = Config()
        result = config.get_preset("nonexistent")
        assert result is None

    def test_get_package_found(self) -> None:
        """Test get_package returns package when found."""
        package = Package(name="git", category="CLI", type="formula")
        config = Config(packages=[package])

        result = config.get_package("git")
        assert result is not None
        assert result.name == "git"

    def test_get_package_not_found(self) -> None:
        """Test get_package returns None when not found."""
        config = Config()
        result = config.get_package("nonexistent")
        assert result is None

    def test_get_packages_by_category(self) -> None:
        """Test get_packages_by_category filters correctly."""
        pkg1 = Package(name="git", category="CLI", type="formula")
        pkg2 = Package(name="node", category="Development", type="formula")
        pkg3 = Package(name="fzf", category="CLI", type="formula")

        config = Config(packages=[pkg1, pkg2, pkg3])

        cli_packages = config.get_packages_by_category("CLI")
        assert len(cli_packages) == 2
        assert all(p.category == "CLI" for p in cli_packages)

    def test_get_packages_by_type(self) -> None:
        """Test get_packages_by_type filters correctly."""
        pkg1 = Package(name="git", category="CLI", type="formula")
        pkg2 = Package(name="vscode", category="IDE", type="cask")
        pkg3 = Package(name="typescript", category="Language", type="npm")

        config = Config(packages=[pkg1, pkg2, pkg3])

        formulae = config.get_packages_by_type("formula")
        casks = config.get_packages_by_type("cask")
        npm = config.get_packages_by_type("npm")

        assert len(formulae) == 1
        assert formulae[0].name == "git"
        assert len(casks) == 1
        assert casks[0].name == "vscode"
        assert len(npm) == 1
        assert npm[0].name == "typescript"

    def test_get_all_categories(self) -> None:
        """Test get_all_categories returns sorted unique categories."""
        pkg1 = Package(name="git", category="CLI", type="formula")
        pkg2 = Package(name="node", category="Development", type="formula")
        pkg3 = Package(name="fzf", category="CLI", type="formula")

        config = Config(packages=[pkg1, pkg2, pkg3])

        categories = config.get_all_categories()
        assert categories == ["CLI", "Development"]
        assert categories == sorted(categories)
