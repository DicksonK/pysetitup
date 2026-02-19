"""Pytest configuration and shared fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_state_file(temp_dir: Path) -> Path:
    """Create a temporary state file path."""
    return temp_dir / "state.json"


@pytest.fixture
def mock_subprocess() -> Generator[AsyncMock, None, None]:
    """Mock asyncio subprocess calls."""
    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate.return_value = (b"output", b"")
    proc.wait.return_value = None

    with pytest.mock.patch("asyncio.create_subprocess_exec", return_value=proc) as mock:
        yield mock


@pytest.fixture
def sample_state_data() -> dict[str, Any]:
    """Sample state data for testing."""
    return {
        "version": "2.0.0",
        "last_updated": "2024-02-14T10:30:00",
        "installed_formulae": ["git", "fzf", "ripgrep"],
        "installed_casks": ["docker", "vscode"],
        "installed_npm": ["typescript", "eslint"],
        "selected_preset": "developer",
        "completed_steps": ["git_config", "packages"],
        "git_configured": True,
        "shell_configured": False,
        "dotfiles_configured": False,
        "macos_configured": False,
    }


@pytest.fixture
def sample_state_file(temp_state_file: Path, sample_state_data: dict[str, Any]) -> Path:
    """Create a sample state file."""
    with open(temp_state_file, "w") as f:
        json.dump(sample_state_data, f)
    return temp_state_file
