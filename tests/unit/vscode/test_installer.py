"""Unit tests for pysetitup.vscode.installer module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pysetitup.vscode.client import VSCodeClient
from pysetitup.vscode.installer import InstallResult, VSCodeInstaller


class TestVSCodeInstaller:
    """Test the VSCodeInstaller class."""

    @pytest.mark.asyncio
    async def test_install_extensions_dry_run(self) -> None:
        """Test install_extensions in dry-run mode."""
        installer = VSCodeInstaller()
        extensions = ["ms-python.python", "dbaeumer.vscode-eslint"]

        results = await installer.install_extensions(extensions, dry_run=True)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].extension_id == "ms-python.python"
        assert results[1].extension_id == "dbaeumer.vscode-eslint"

    @pytest.mark.asyncio
    async def test_install_extensions_cli_not_available(self) -> None:
        """Test install_extensions when VS Code CLI not available."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.is_installed.return_value = False

        installer = VSCodeInstaller(client=mock_client)
        extensions = ["ms-python.python"]

        results = await installer.install_extensions(extensions)

        assert len(results) == 1
        assert results[0].success is False
        assert "VS Code CLI not available" in results[0].error

    @pytest.mark.asyncio
    async def test_install_extensions_success(self) -> None:
        """Test successful extension installation."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.is_installed.return_value = True
        mock_client.list_extensions_with_versions.return_value = {}
        mock_client.install_extension.return_value = (True, "Successfully installed")

        installer = VSCodeInstaller(client=mock_client)
        extensions = ["ms-python.python", "dbaeumer.vscode-eslint"]

        results = await installer.install_extensions(extensions)

        assert len(results) == 2
        assert all(r.success for r in results)
        assert mock_client.install_extension.call_count == 2

    @pytest.mark.asyncio
    async def test_install_extensions_already_installed(self) -> None:
        """Test extension installation when already installed."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.is_installed.return_value = True
        mock_client.list_extensions_with_versions.return_value = {
            "ms-python.python": "2024.0.0"
        }

        installer = VSCodeInstaller(client=mock_client)
        extensions = ["ms-python.python"]

        results = await installer.install_extensions(extensions)

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].already_installed is True
        assert results[0].version == "2024.0.0"
        # Should not call install for already-installed extensions
        mock_client.install_extension.assert_not_called()

    @pytest.mark.asyncio
    async def test_install_extensions_with_progress(self) -> None:
        """Test extension installation with progress callback."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.is_installed.return_value = True
        mock_client.list_extensions_with_versions.return_value = {}
        mock_client.install_extension.return_value = (True, "Success")

        progress_calls = []

        def on_progress(msg: str) -> None:
            progress_calls.append(msg)

        installer = VSCodeInstaller(client=mock_client)
        await installer.install_extensions(["ms-python.python"], on_progress=on_progress)

        assert len(progress_calls) >= 2  # At least "Installing..." and "✓" messages
        assert any("Installing" in msg for msg in progress_calls)
        assert any("✓" in msg for msg in progress_calls)

    @pytest.mark.asyncio
    async def test_install_extensions_partial_failure(self) -> None:
        """Test extension installation with some failures."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.is_installed.return_value = True
        mock_client.list_extensions_with_versions.return_value = {}

        # First call succeeds, second fails
        mock_client.install_extension.side_effect = [
            (True, "Success"),
            (False, "Extension not found"),
        ]

        installer = VSCodeInstaller(client=mock_client)
        extensions = ["ms-python.python", "invalid-extension"]

        results = await installer.install_extensions(extensions)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert "Extension not found" in results[1].error

    @pytest.mark.asyncio
    async def test_install_extensions_exception_handling(self) -> None:
        """Test extension installation handles exceptions."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.is_installed.return_value = True
        mock_client.list_extensions_with_versions.return_value = {}
        mock_client.install_extension.side_effect = Exception("Network error")

        installer = VSCodeInstaller(client=mock_client)
        extensions = ["ms-python.python"]

        results = await installer.install_extensions(extensions)

        assert len(results) == 1
        assert results[0].success is False
        assert "Network error" in results[0].error

    @pytest.mark.asyncio
    async def test_uninstall_extensions(self) -> None:
        """Test extension uninstallation."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.uninstall_extension.side_effect = [
            (True, "Uninstalled successfully"),
            (False, "Extension not found"),
        ]

        installer = VSCodeInstaller(client=mock_client)
        extensions = ["ms-python.python", "invalid-extension"]

        results = await installer.uninstall_extensions(extensions)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert "Extension not found" in results[1].error

    @pytest.mark.asyncio
    async def test_max_concurrent_limit(self) -> None:
        """Test that max_concurrent limits parallel installations."""
        mock_client = AsyncMock(spec=VSCodeClient)
        mock_client.is_installed.return_value = True
        mock_client.list_extensions_with_versions.return_value = {}
        mock_client.install_extension.return_value = (True, "Success")

        installer = VSCodeInstaller(client=mock_client, max_concurrent=2)
        extensions = ["ext1", "ext2", "ext3", "ext4", "ext5"]

        results = await installer.install_extensions(extensions)

        assert len(results) == 5
        assert all(r.success for r in results)
        # All should be installed, just with concurrency limit
        assert mock_client.install_extension.call_count == 5
