"""Unit tests for pysetitup.vscode.client module."""

from unittest.mock import AsyncMock, patch

import pytest

from pysetitup.utils.errors import CommandError
from pysetitup.vscode.client import VSCodeClient


class TestVSCodeClient:
    """Test the VSCodeClient class."""

    @pytest.mark.asyncio
    async def test_list_extensions(self) -> None:
        """Test list_extensions returns extension IDs."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (
            b"ms-python.python\ndbaeumer.vscode-eslint\nesbenp.prettier-vscode\n",
            b"",
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            extensions = await client.list_extensions()

        assert len(extensions) == 3
        assert "ms-python.python" in extensions
        assert "dbaeumer.vscode-eslint" in extensions
        assert "esbenp.prettier-vscode" in extensions

    @pytest.mark.asyncio
    async def test_list_extensions_with_versions(self) -> None:
        """Test list_extensions_with_versions returns dict with versions."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (
            b"ms-python.python@2024.0.0\ndbaeumer.vscode-eslint@2.4.4\n",
            b"",
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            extensions = await client.list_extensions_with_versions()

        assert len(extensions) == 2
        assert extensions["ms-python.python"] == "2024.0.0"
        assert extensions["dbaeumer.vscode-eslint"] == "2.4.4"

    @pytest.mark.asyncio
    async def test_install_extension_success(self) -> None:
        """Test install_extension succeeds."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (
            b"Extension 'ms-python.python' v2024.0.0 was successfully installed.",
            b"",
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_extension("ms-python.python")

        assert success is True
        assert "Successfully installed" in message

    @pytest.mark.asyncio
    async def test_install_extension_already_installed(self) -> None:
        """Test install_extension detects already installed."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (
            b"Extension 'ms-python.python' is already installed.",
            b"",
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_extension("ms-python.python")

        assert success is True
        assert "already installed" in message.lower()

    @pytest.mark.asyncio
    async def test_install_extension_failure(self) -> None:
        """Test install_extension handles failure."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"Extension not found")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_extension("invalid-extension")

        assert success is False
        assert "Failed to install" in message

    @pytest.mark.asyncio
    async def test_uninstall_extension_success(self) -> None:
        """Test uninstall_extension succeeds."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"Extension uninstalled", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.uninstall_extension("ms-python.python")

        assert success is True
        assert "Successfully uninstalled" in message

    @pytest.mark.asyncio
    async def test_is_installed_true(self) -> None:
        """Test is_installed returns True when CLI available."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"1.85.0", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            installed = await client.is_installed()

        assert installed is True

    @pytest.mark.asyncio
    async def test_is_installed_false(self) -> None:
        """Test is_installed returns False when CLI not available."""
        client = VSCodeClient()

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("command not found"),
        ):
            # Mock the _run_command to return False
            with patch.object(client, "_run_command", side_effect=CommandError("VS Code CLI not found")):
                installed = await client.is_installed()

        assert installed is False

    @pytest.mark.asyncio
    async def test_get_version(self) -> None:
        """Test get_version returns version string."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (
            b"1.85.0\ncommit-hash\narch\n",
            b"",
        )

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            version = await client.get_version()

        assert version == "1.85.0"

    @pytest.mark.asyncio
    async def test_code_command_not_found(self) -> None:
        """Test error when code command not in PATH."""
        client = VSCodeClient()

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("command not found"),
        ):
            with pytest.raises(CommandError) as exc_info:
                await client.list_extensions()

        assert "VS Code CLI not found" in str(exc_info.value)
        assert "Shell Command: Install 'code' command in PATH" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_install_with_force_flag(self) -> None:
        """Test install_extension with force=True adds --force flag."""
        client = VSCodeClient()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"Installed", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            await client.install_extension("ms-python.python", force=True)

        # Verify --force flag was passed
        call_args = mock_exec.call_args[0]
        assert "--force" in call_args
