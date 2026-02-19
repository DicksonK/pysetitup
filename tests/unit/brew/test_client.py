"""Unit tests for pysetitup.brew.client module."""

from unittest.mock import AsyncMock, patch

import pytest

from pysetitup.brew.client import BrewClient
from pysetitup.utils.errors import DependencyError, InstallationError


class TestBrewClient:
    """Test the BrewClient class."""

    def test_init_finds_brew(self) -> None:
        """Test BrewClient initialization finds brew in PATH."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()
            assert client.brew_path == "/usr/local/bin/brew"

    def test_init_raises_if_brew_not_found(self) -> None:
        """Test BrewClient raises error if brew not installed."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(DependencyError) as exc_info:
                BrewClient()

            assert "not installed" in str(exc_info.value).lower()

    def test_init_with_custom_path(self) -> None:
        """Test BrewClient accepts custom brew path."""
        client = BrewClient(brew_path="/custom/path/brew")
        assert client.brew_path == "/custom/path/brew"

    @pytest.mark.asyncio
    async def test_run_command_success(self) -> None:
        """Test _run_command executes successfully."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"output", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            returncode, stdout, stderr = await client._run_command(["list"])

            assert returncode == 0
            assert stdout == "output"
            assert stderr == ""

    @pytest.mark.asyncio
    async def test_run_command_with_error(self) -> None:
        """Test _run_command raises on non-zero exit code."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"error message")
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(InstallationError) as exc_info:
                await client._run_command(["bad-command"], check=True)

            assert "failed" in str(exc_info.value).lower()
            assert "error message" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_command_no_check(self) -> None:
        """Test _run_command with check=False doesn't raise."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"error")
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            returncode, stdout, stderr = await client._run_command(["bad-command"], check=False)

            assert returncode == 1
            assert stderr == "error"

    @pytest.mark.asyncio
    async def test_install_formula_success(self) -> None:
        """Test install_formula successfully installs a package."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Installed git", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_formula("git")

            assert success is True
            assert "git" in message.lower()

    @pytest.mark.asyncio
    async def test_install_formula_failure(self) -> None:
        """Test install_formula handles installation failure."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"Package not found")
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_formula("nonexistent")

            assert success is False
            assert "failed" in message.lower()

    @pytest.mark.asyncio
    async def test_install_cask_success(self) -> None:
        """Test install_cask successfully installs a cask."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Installed docker", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_cask("docker")

            assert success is True
            assert "docker" in message.lower()

    @pytest.mark.asyncio
    async def test_tap_success(self) -> None:
        """Test tap successfully adds a repository."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Tapped homebrew/cask", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.tap("homebrew/cask")

            assert success is True
            assert "homebrew/cask" in message.lower()

    @pytest.mark.asyncio
    async def test_list_formulae(self) -> None:
        """Test list_formulae returns installed packages."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"git\nnode\npython@3.11\n", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            formulae = await client.list_formulae()

            assert formulae == ["git", "node", "python@3.11"]

    @pytest.mark.asyncio
    async def test_list_formulae_empty(self) -> None:
        """Test list_formulae returns empty list when none installed."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            formulae = await client.list_formulae()

            assert formulae == []

    @pytest.mark.asyncio
    async def test_list_casks(self) -> None:
        """Test list_casks returns installed casks."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"docker\nvscode\n", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            casks = await client.list_casks()

            assert casks == ["docker", "vscode"]

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test update successfully updates Homebrew."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Updated Homebrew", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.update()

            assert success is True
            assert "updated" in message.lower()

    @pytest.mark.asyncio
    async def test_upgrade_all(self) -> None:
        """Test upgrade without package name upgrades all."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Upgraded packages", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.upgrade()

            assert success is True
            assert "all" in message.lower()

    @pytest.mark.asyncio
    async def test_upgrade_specific_package(self) -> None:
        """Test upgrade with package name upgrades that package."""
        with patch("shutil.which", return_value="/usr/local/bin/brew"):
            client = BrewClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Upgraded git", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.upgrade("git")

            assert success is True
            assert "git" in message.lower()
