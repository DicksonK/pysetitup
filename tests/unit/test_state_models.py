"""Unit tests for pysetitup.state.models module."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from pysetitup.state.models import InstallState, PackageType


class TestPackageType:
    """Test the PackageType enum."""

    def test_package_type_values(self) -> None:
        """Test PackageType enum values."""
        assert PackageType.FORMULA == "formula"
        assert PackageType.CASK == "cask"
        assert PackageType.NPM == "npm"
        assert PackageType.VSCODE == "vscode"

    def test_package_type_members(self) -> None:
        """Test PackageType has expected members."""
        assert set(PackageType) == {
            PackageType.FORMULA,
            PackageType.CASK,
            PackageType.NPM,
            PackageType.VSCODE,
        }


class TestInstallState:
    """Test the InstallState model."""

    def test_default_state(self) -> None:
        """Test InstallState with default values."""
        state = InstallState()
        assert state.version == "2.0.0"
        assert isinstance(state.last_updated, datetime)
        assert state.installed_formulae == []
        assert state.installed_casks == []
        assert state.installed_npm == []
        assert state.selected_preset is None
        assert state.completed_steps == []
        assert state.git_configured is False
        assert state.shell_configured is False
        assert state.dotfiles_configured is False
        assert state.macos_configured is False

    def test_state_with_data(self) -> None:
        """Test InstallState with provided data."""
        now = datetime.now()
        state = InstallState(
            version="2.0.0",
            last_updated=now,
            installed_formulae=["git", "fzf"],
            installed_casks=["docker"],
            installed_npm=["typescript"],
            selected_preset="developer",
            completed_steps=["git_config"],
            git_configured=True,
            shell_configured=False,
            dotfiles_configured=False,
            macos_configured=False,
        )

        assert state.version == "2.0.0"
        assert state.last_updated == now
        assert state.installed_formulae == ["git", "fzf"]
        assert state.installed_casks == ["docker"]
        assert state.installed_npm == ["typescript"]
        assert state.selected_preset == "developer"
        assert state.completed_steps == ["git_config"]
        assert state.git_configured is True

    def test_state_json_serialization(self) -> None:
        """Test InstallState can be serialized to JSON."""
        state = InstallState(
            installed_formulae=["git"],
            installed_casks=["vscode"],
            selected_preset="minimal",
        )

        # Serialize to dict
        data = state.model_dump(mode="json")

        assert data["version"] == "2.0.0"
        assert "last_updated" in data
        assert data["installed_formulae"] == ["git"]
        assert data["installed_casks"] == ["vscode"]
        assert data["selected_preset"] == "minimal"

    def test_state_json_deserialization(self) -> None:
        """Test InstallState can be deserialized from JSON."""
        data = {
            "version": "2.0.0",
            "last_updated": "2024-02-14T10:30:00",
            "installed_formulae": ["git", "fzf"],
            "installed_casks": ["docker"],
            "installed_npm": ["eslint"],
            "selected_preset": "developer",
            "completed_steps": ["git_config", "packages"],
            "git_configured": True,
            "shell_configured": False,
            "dotfiles_configured": False,
            "macos_configured": False,
        }

        state = InstallState.model_validate(data)

        assert state.version == "2.0.0"
        assert state.installed_formulae == ["git", "fzf"]
        assert state.installed_casks == ["docker"]
        assert state.installed_npm == ["eslint"]
        assert state.selected_preset == "developer"
        assert state.completed_steps == ["git_config", "packages"]
        assert state.git_configured is True

    def test_state_datetime_parsing(self) -> None:
        """Test InstallState parses datetime from ISO8601 string."""
        data = {
            "version": "2.0.0",
            "last_updated": "2024-02-14T10:30:00.123456",
        }

        state = InstallState.model_validate(data)
        assert isinstance(state.last_updated, datetime)
        assert state.last_updated.year == 2024
        assert state.last_updated.month == 2
        assert state.last_updated.day == 14

    def test_state_validation_requires_valid_fields(self) -> None:
        """Test InstallState validates field types."""
        # Invalid type for installed_formulae
        with pytest.raises(ValidationError):
            InstallState(installed_formulae="not-a-list")  # type: ignore

        # Invalid type for version (should be string)
        with pytest.raises(ValidationError):
            InstallState(version=123)  # type: ignore

    def test_state_roundtrip(self) -> None:
        """Test InstallState can be serialized and deserialized."""
        original = InstallState(
            installed_formulae=["git", "fzf", "ripgrep"],
            installed_casks=["docker", "vscode"],
            installed_npm=["typescript", "eslint"],
            selected_preset="full",
            completed_steps=["git_config", "packages", "npm"],
            git_configured=True,
            shell_configured=True,
        )

        # Serialize
        data = original.model_dump(mode="json")

        # Deserialize
        restored = InstallState.model_validate(data)

        # Compare (excluding last_updated which will differ)
        assert restored.version == original.version
        assert restored.installed_formulae == original.installed_formulae
        assert restored.installed_casks == original.installed_casks
        assert restored.installed_npm == original.installed_npm
        assert restored.selected_preset == original.selected_preset
        assert restored.completed_steps == original.completed_steps
        assert restored.git_configured == original.git_configured
        assert restored.shell_configured == original.shell_configured
