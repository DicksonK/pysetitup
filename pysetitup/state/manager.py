"""State management for PySetItUp."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from pysetitup.state.models import InstallState, PackageType
from pysetitup.system.env import ensure_pysetitup_dir
from pysetitup.utils.errors import StateError


class StateManager:
    """Manages PySetItUp installation state persistence."""

    def __init__(self, state_file: Optional[str] = None) -> None:
        """
        Initialize the state manager.

        Args:
            state_file: Optional custom path to state file.
                       Defaults to ~/.pysetitup/state.json
        """
        if state_file:
            self.state_file = Path(state_file)
        else:
            pysetitup_dir = ensure_pysetitup_dir()
            self.state_file = Path(pysetitup_dir) / "state.json"

        self._state: Optional[InstallState] = None

    def load_state(self) -> InstallState:
        """
        Load state from file or create new state if file doesn't exist.

        Returns:
            Current installation state

        Raises:
            StateError: If state file exists but cannot be parsed
        """
        if not self.state_file.exists():
            self._state = InstallState()
            return self._state

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                self._state = InstallState.model_validate(data)
                return self._state
        except Exception as e:
            raise StateError(f"Failed to load state from {self.state_file}: {e}")

    def save_state(self, state: Optional[InstallState] = None) -> None:
        """
        Save state to file.

        Args:
            state: State to save. If None, saves current state.

        Raises:
            StateError: If state cannot be saved
        """
        if state is None:
            if self._state is None:
                self._state = InstallState()
            state = self._state

        # Update timestamp
        state.last_updated = datetime.now()

        # Ensure directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.state_file, "w") as f:
                json.dump(
                    state.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
        except Exception as e:
            raise StateError(f"Failed to save state to {self.state_file}: {e}")

    def get_state(self) -> InstallState:
        """
        Get current state, loading from file if not already loaded.

        Returns:
            Current installation state
        """
        if self._state is None:
            return self.load_state()
        return self._state

    def mark_installed(self, package: str, package_type: PackageType) -> None:
        """
        Mark a package as installed.

        Args:
            package: Package name
            package_type: Type of package (formula, cask, npm, vscode)
        """
        state = self.get_state()

        if package_type == PackageType.FORMULA:
            if package not in state.installed_formulae:
                state.installed_formulae.append(package)
        elif package_type == PackageType.CASK:
            if package not in state.installed_casks:
                state.installed_casks.append(package)
        elif package_type == PackageType.NPM:
            if package not in state.installed_npm:
                state.installed_npm.append(package)
        elif package_type == PackageType.VSCODE:
            if package not in state.installed_vscode:
                state.installed_vscode.append(package)

        self.save_state(state)

    def mark_uninstalled(self, package: str, package_type: PackageType) -> None:
        """
        Mark a package as uninstalled.

        Args:
            package: Package name
            package_type: Type of package (formula, cask, npm, vscode)
        """
        state = self.get_state()

        if package_type == PackageType.FORMULA and package in state.installed_formulae:
            state.installed_formulae.remove(package)
        elif package_type == PackageType.CASK and package in state.installed_casks:
            state.installed_casks.remove(package)
        elif package_type == PackageType.NPM and package in state.installed_npm:
            state.installed_npm.remove(package)
        elif package_type == PackageType.VSCODE and package in state.installed_vscode:
            state.installed_vscode.remove(package)

        self.save_state(state)

    def is_installed(self, package: str, package_type: PackageType) -> bool:
        """
        Check if a package is marked as installed.

        Args:
            package: Package name
            package_type: Type of package

        Returns:
            True if package is installed
        """
        state = self.get_state()

        if package_type == PackageType.FORMULA:
            return package in state.installed_formulae
        elif package_type == PackageType.CASK:
            return package in state.installed_casks
        elif package_type == PackageType.NPM:
            return package in state.installed_npm
        elif package_type == PackageType.VSCODE:
            return package in state.installed_vscode

        return False

    def mark_step_complete(self, step_name: str) -> None:
        """
        Mark an installation step as complete.

        Args:
            step_name: Name of the completed step
        """
        state = self.get_state()
        if step_name not in state.completed_steps:
            state.completed_steps.append(step_name)
        self.save_state(state)

    def is_step_complete(self, step_name: str) -> bool:
        """
        Check if an installation step is complete.

        Args:
            step_name: Name of the step

        Returns:
            True if step is complete
        """
        state = self.get_state()
        return step_name in state.completed_steps

    def set_selected_preset(self, preset: str) -> None:
        """
        Set the selected preset.

        Args:
            preset: Preset name
        """
        state = self.get_state()
        state.selected_preset = preset
        self.save_state(state)

    def reset_state(self) -> None:
        """Reset state to empty (useful for testing or fresh installs)."""
        self._state = InstallState()
        self.save_state(self._state)
