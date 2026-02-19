"""Unit tests for pysetitup.state.manager module."""

import json
from pathlib import Path

import pytest

from pysetitup.state.manager import StateManager
from pysetitup.state.models import InstallState, PackageType
from pysetitup.utils.errors import StateError


class TestStateManagerInit:
    """Test StateManager initialization."""

    def test_init_with_custom_path(self, temp_state_file: Path) -> None:
        """Test StateManager can be initialized with custom path."""
        manager = StateManager(state_file=str(temp_state_file))
        assert manager.state_file == temp_state_file

    def test_init_with_default_path(self) -> None:
        """Test StateManager uses default path when none provided."""
        manager = StateManager()
        assert str(manager.state_file).endswith(".pysetitup/state.json")


class TestStateLoading:
    """Test state loading functionality."""

    def test_load_state_creates_new_when_missing(self, temp_state_file: Path) -> None:
        """Test load_state creates new state when file doesn't exist."""
        manager = StateManager(state_file=str(temp_state_file))
        state = manager.load_state()

        assert isinstance(state, InstallState)
        assert state.version == "2.0.0"
        assert state.installed_formulae == []
        assert state.installed_casks == []

    def test_load_state_from_existing_file(self, sample_state_file: Path) -> None:
        """Test load_state reads from existing file."""
        manager = StateManager(state_file=str(sample_state_file))
        state = manager.load_state()

        assert state.installed_formulae == ["git", "fzf", "ripgrep"]
        assert state.installed_casks == ["docker", "vscode"]
        assert state.installed_npm == ["typescript", "eslint"]
        assert state.selected_preset == "developer"

    def test_load_state_with_invalid_json(self, temp_state_file: Path) -> None:
        """Test load_state raises StateError on invalid JSON."""
        # Write invalid JSON
        temp_state_file.write_text("{ invalid json }")

        manager = StateManager(state_file=str(temp_state_file))
        with pytest.raises(StateError) as exc_info:
            manager.load_state()
        assert "Failed to load state" in str(exc_info.value)

    def test_get_state_loads_if_not_cached(self, sample_state_file: Path) -> None:
        """Test get_state loads from file if not already cached."""
        manager = StateManager(state_file=str(sample_state_file))
        assert manager._state is None

        state = manager.get_state()
        assert manager._state is not None
        assert state.installed_formulae == ["git", "fzf", "ripgrep"]

    def test_get_state_returns_cached(self, temp_state_file: Path) -> None:
        """Test get_state returns cached state on subsequent calls."""
        manager = StateManager(state_file=str(temp_state_file))

        state1 = manager.get_state()
        state2 = manager.get_state()

        # Should be the same object
        assert state1 is state2


class TestStateSaving:
    """Test state saving functionality."""

    def test_save_state_creates_file(self, temp_state_file: Path) -> None:
        """Test save_state creates file if it doesn't exist."""
        manager = StateManager(state_file=str(temp_state_file))
        state = InstallState(installed_formulae=["git"])

        manager.save_state(state)

        assert temp_state_file.exists()

    def test_save_state_writes_json(self, temp_state_file: Path) -> None:
        """Test save_state writes valid JSON."""
        manager = StateManager(state_file=str(temp_state_file))
        state = InstallState(
            installed_formulae=["git", "fzf"],
            installed_casks=["docker"],
            selected_preset="developer",
        )

        manager.save_state(state)

        # Read and validate JSON
        with open(temp_state_file) as f:
            data = json.load(f)

        assert data["installed_formulae"] == ["git", "fzf"]
        assert data["installed_casks"] == ["docker"]
        assert data["selected_preset"] == "developer"

    def test_save_state_updates_timestamp(self, temp_state_file: Path) -> None:
        """Test save_state updates the last_updated timestamp."""
        manager = StateManager(state_file=str(temp_state_file))
        state = InstallState()

        original_time = state.last_updated
        manager.save_state(state)

        # Timestamp should be updated
        assert state.last_updated > original_time

    def test_save_state_without_argument(self, temp_state_file: Path) -> None:
        """Test save_state can save internal state without argument."""
        manager = StateManager(state_file=str(temp_state_file))
        manager.load_state()
        manager._state.installed_formulae.append("git")  # type: ignore

        manager.save_state()

        # Reload and verify
        manager2 = StateManager(state_file=str(temp_state_file))
        state = manager2.load_state()
        assert "git" in state.installed_formulae

    def test_save_state_creates_parent_directory(self, temp_dir: Path) -> None:
        """Test save_state creates parent directories if needed."""
        nested_file = temp_dir / "nested" / "dir" / "state.json"
        manager = StateManager(state_file=str(nested_file))

        state = InstallState()
        manager.save_state(state)

        assert nested_file.exists()
        assert nested_file.parent.exists()


class TestPackageTracking:
    """Test package installation tracking."""

    def test_mark_installed_formula(self, temp_state_file: Path) -> None:
        """Test marking a formula as installed."""
        manager = StateManager(state_file=str(temp_state_file))
        manager.mark_installed("git", PackageType.FORMULA)

        state = manager.get_state()
        assert "git" in state.installed_formulae
        assert state.installed_casks == []
        assert state.installed_npm == []

    def test_mark_installed_cask(self, temp_state_file: Path) -> None:
        """Test marking a cask as installed."""
        manager = StateManager(state_file=str(temp_state_file))
        manager.mark_installed("docker", PackageType.CASK)

        state = manager.get_state()
        assert "docker" in state.installed_casks
        assert state.installed_formulae == []

    def test_mark_installed_npm(self, temp_state_file: Path) -> None:
        """Test marking an npm package as installed."""
        manager = StateManager(state_file=str(temp_state_file))
        manager.mark_installed("typescript", PackageType.NPM)

        state = manager.get_state()
        assert "typescript" in state.installed_npm

    def test_mark_installed_prevents_duplicates(self, temp_state_file: Path) -> None:
        """Test mark_installed doesn't add duplicates."""
        manager = StateManager(state_file=str(temp_state_file))

        manager.mark_installed("git", PackageType.FORMULA)
        manager.mark_installed("git", PackageType.FORMULA)
        manager.mark_installed("git", PackageType.FORMULA)

        state = manager.get_state()
        assert state.installed_formulae.count("git") == 1

    def test_mark_uninstalled_formula(self, sample_state_file: Path) -> None:
        """Test marking a formula as uninstalled."""
        manager = StateManager(state_file=str(sample_state_file))
        manager.mark_uninstalled("git", PackageType.FORMULA)

        state = manager.get_state()
        assert "git" not in state.installed_formulae
        assert "fzf" in state.installed_formulae  # Others remain

    def test_mark_uninstalled_cask(self, sample_state_file: Path) -> None:
        """Test marking a cask as uninstalled."""
        manager = StateManager(state_file=str(sample_state_file))
        manager.mark_uninstalled("docker", PackageType.CASK)

        state = manager.get_state()
        assert "docker" not in state.installed_casks
        assert "vscode" in state.installed_casks

    def test_mark_uninstalled_npm(self, sample_state_file: Path) -> None:
        """Test marking an npm package as uninstalled."""
        manager = StateManager(state_file=str(sample_state_file))
        manager.mark_uninstalled("typescript", PackageType.NPM)

        state = manager.get_state()
        assert "typescript" not in state.installed_npm
        assert "eslint" in state.installed_npm

    def test_mark_uninstalled_nonexistent(self, temp_state_file: Path) -> None:
        """Test mark_uninstalled handles nonexistent packages gracefully."""
        manager = StateManager(state_file=str(temp_state_file))
        # Should not raise
        manager.mark_uninstalled("nonexistent", PackageType.FORMULA)

    def test_is_installed_formula(self, sample_state_file: Path) -> None:
        """Test checking if a formula is installed."""
        manager = StateManager(state_file=str(sample_state_file))

        assert manager.is_installed("git", PackageType.FORMULA) is True
        assert manager.is_installed("fzf", PackageType.FORMULA) is True
        assert manager.is_installed("nonexistent", PackageType.FORMULA) is False

    def test_is_installed_cask(self, sample_state_file: Path) -> None:
        """Test checking if a cask is installed."""
        manager = StateManager(state_file=str(sample_state_file))

        assert manager.is_installed("docker", PackageType.CASK) is True
        assert manager.is_installed("chrome", PackageType.CASK) is False

    def test_is_installed_npm(self, sample_state_file: Path) -> None:
        """Test checking if an npm package is installed."""
        manager = StateManager(state_file=str(sample_state_file))

        assert manager.is_installed("typescript", PackageType.NPM) is True
        assert manager.is_installed("webpack", PackageType.NPM) is False


class TestStepTracking:
    """Test installation step tracking."""

    def test_mark_step_complete(self, temp_state_file: Path) -> None:
        """Test marking a step as complete."""
        manager = StateManager(state_file=str(temp_state_file))
        manager.mark_step_complete("git_config")

        state = manager.get_state()
        assert "git_config" in state.completed_steps

    def test_mark_step_complete_prevents_duplicates(self, temp_state_file: Path) -> None:
        """Test mark_step_complete doesn't add duplicates."""
        manager = StateManager(state_file=str(temp_state_file))

        manager.mark_step_complete("git_config")
        manager.mark_step_complete("git_config")

        state = manager.get_state()
        assert state.completed_steps.count("git_config") == 1

    def test_is_step_complete(self, sample_state_file: Path) -> None:
        """Test checking if a step is complete."""
        manager = StateManager(state_file=str(sample_state_file))

        assert manager.is_step_complete("git_config") is True
        assert manager.is_step_complete("packages") is True
        assert manager.is_step_complete("nonexistent") is False


class TestPresetManagement:
    """Test preset management."""

    def test_set_selected_preset(self, temp_state_file: Path) -> None:
        """Test setting the selected preset."""
        manager = StateManager(state_file=str(temp_state_file))
        manager.set_selected_preset("developer")

        state = manager.get_state()
        assert state.selected_preset == "developer"

    def test_set_selected_preset_overwrites(self, temp_state_file: Path) -> None:
        """Test setting preset overwrites previous value."""
        manager = StateManager(state_file=str(temp_state_file))

        manager.set_selected_preset("minimal")
        manager.set_selected_preset("full")

        state = manager.get_state()
        assert state.selected_preset == "full"


class TestStateReset:
    """Test state reset functionality."""

    def test_reset_state(self, sample_state_file: Path) -> None:
        """Test reset_state clears all state."""
        manager = StateManager(state_file=str(sample_state_file))

        # Load existing state
        old_state = manager.load_state()
        assert len(old_state.installed_formulae) > 0

        # Reset
        manager.reset_state()

        # Verify it's empty
        new_state = manager.get_state()
        assert new_state.installed_formulae == []
        assert new_state.installed_casks == []
        assert new_state.installed_npm == []
        assert new_state.completed_steps == []
        assert new_state.selected_preset is None

    def test_reset_state_persists(self, sample_state_file: Path) -> None:
        """Test reset_state persists to file."""
        manager = StateManager(state_file=str(sample_state_file))
        manager.reset_state()

        # Create new manager and load
        manager2 = StateManager(state_file=str(sample_state_file))
        state = manager2.load_state()

        assert state.installed_formulae == []
        assert state.installed_casks == []


class TestStatePersistence:
    """Test state persistence across manager instances."""

    def test_state_persists_across_instances(self, temp_state_file: Path) -> None:
        """Test state changes persist when using different manager instances."""
        # First manager: mark some packages as installed
        manager1 = StateManager(state_file=str(temp_state_file))
        manager1.mark_installed("git", PackageType.FORMULA)
        manager1.mark_installed("docker", PackageType.CASK)
        manager1.set_selected_preset("developer")

        # Second manager: verify state persisted
        manager2 = StateManager(state_file=str(temp_state_file))
        state = manager2.load_state()

        assert "git" in state.installed_formulae
        assert "docker" in state.installed_casks
        assert state.selected_preset == "developer"

    def test_multiple_operations_persist(self, temp_state_file: Path) -> None:
        """Test multiple state operations persist correctly."""
        manager = StateManager(state_file=str(temp_state_file))

        # Perform multiple operations
        manager.mark_installed("git", PackageType.FORMULA)
        manager.mark_installed("fzf", PackageType.FORMULA)
        manager.mark_installed("docker", PackageType.CASK)
        manager.mark_step_complete("git_config")
        manager.mark_step_complete("packages")
        manager.set_selected_preset("full")

        # Reload and verify
        manager2 = StateManager(state_file=str(temp_state_file))
        state = manager2.load_state()

        assert set(state.installed_formulae) == {"git", "fzf"}
        assert state.installed_casks == ["docker"]
        assert set(state.completed_steps) == {"git_config", "packages"}
        assert state.selected_preset == "full"
