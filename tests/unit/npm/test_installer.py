"""Unit tests for pysetitup.npm.installer module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from pysetitup.npm.installer import NpmInstaller


class TestNpmInstaller:
    """Test the NpmInstaller class."""

    @pytest.mark.asyncio
    async def test_install_packages_batch_success(self) -> None:
        """Test install_packages successfully installs via batch."""
        mock_client = MagicMock()
        mock_client.install_global = AsyncMock(return_value=(True, "added 3 packages"))

        installer = NpmInstaller(client=mock_client)
        results = await installer.install_packages(["typescript", "eslint", "prettier"])

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.batch for r in results)
        mock_client.install_global.assert_called_once()

    @pytest.mark.asyncio
    async def test_install_packages_batch_retry_success(self) -> None:
        """Test install_packages retries batch and succeeds on 2nd attempt."""
        mock_client = MagicMock()
        # First call fails, second succeeds
        mock_client.install_global = AsyncMock(
            side_effect=[
                (False, "Network error"),
                (True, "added 2 packages"),
            ]
        )

        installer = NpmInstaller(client=mock_client, max_retries=3)
        results = await installer.install_packages(["typescript", "eslint"])

        assert len(results) == 2
        assert all(r.success for r in results)
        assert all(r.batch for r in results)
        assert mock_client.install_global.call_count == 2

    @pytest.mark.asyncio
    async def test_install_packages_batch_fallback_to_sequential(self) -> None:
        """Test install_packages falls back to sequential after batch fails."""
        mock_client = MagicMock()
        # Batch install always fails
        mock_client.install_global = AsyncMock(return_value=(False, "Batch failed"))
        # Sequential installs succeed
        mock_client.install_single = AsyncMock(return_value=(True, "Installed"))

        installer = NpmInstaller(client=mock_client, max_retries=2)
        results = await installer.install_packages(["typescript", "eslint"])

        assert len(results) == 2
        assert all(r.success for r in results)
        assert not any(r.batch for r in results)  # Sequential, not batch
        # Batch tried max_retries times
        assert mock_client.install_global.call_count == 2
        # Then fell back to sequential (2 packages)
        assert mock_client.install_single.call_count == 2

    @pytest.mark.asyncio
    async def test_install_packages_batch_exception_fallback(self) -> None:
        """Test install_packages falls back on exception."""
        mock_client = MagicMock()
        # Batch install raises exception
        mock_client.install_global = AsyncMock(side_effect=Exception("Connection timeout"))
        # Sequential installs succeed
        mock_client.install_single = AsyncMock(return_value=(True, "Installed"))

        installer = NpmInstaller(client=mock_client, max_retries=2)
        results = await installer.install_packages(["typescript"])

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].batch is False
        # Batch tried max_retries times (all exceptions)
        assert mock_client.install_global.call_count == 2
        # Then fell back to sequential
        assert mock_client.install_single.call_count == 1

    @pytest.mark.asyncio
    async def test_install_packages_empty_list(self) -> None:
        """Test install_packages with empty list returns empty results."""
        mock_client = MagicMock()

        installer = NpmInstaller(client=mock_client)
        results = await installer.install_packages([])

        assert results == []
        mock_client.install_global.assert_not_called()

    @pytest.mark.asyncio
    async def test_install_packages_with_progress_callback(self) -> None:
        """Test install_packages calls progress callback for batch."""
        mock_client = MagicMock()
        mock_client.install_global = AsyncMock(return_value=(True, "added 2 packages"))

        progress_calls = []

        def on_progress(pkg: str, status: str) -> None:
            progress_calls.append((pkg, status))

        installer = NpmInstaller(client=mock_client)
        await installer.install_packages(["typescript", "eslint"], on_progress=on_progress)

        # Should have progress calls for batch install
        assert len(progress_calls) >= 1
        assert ("npm", "Installing 2 packages (batch)...") in progress_calls
        assert ("npm", "✓ Installed 2 packages") in progress_calls

    @pytest.mark.asyncio
    async def test_install_sequential_success(self) -> None:
        """Test _install_sequential installs all packages."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(return_value=(True, "Installed"))

        installer = NpmInstaller(client=mock_client)
        results = await installer._install_sequential(["typescript", "eslint"])

        assert len(results) == 2
        assert all(r.success for r in results)
        assert not any(r.batch for r in results)
        assert mock_client.install_single.call_count == 2

    @pytest.mark.asyncio
    async def test_install_sequential_already_installed(self) -> None:
        """Test _install_sequential detects already installed packages."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(return_value=(True, "already installed typescript@5.0.0"))

        installer = NpmInstaller(client=mock_client)
        results = await installer._install_sequential(["typescript"])

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].already_installed is True

    @pytest.mark.asyncio
    async def test_install_sequential_mixed_results(self) -> None:
        """Test _install_sequential handles mixed success/failure."""
        mock_client = MagicMock()

        async def install_side_effect(pkg, timeout):
            if pkg == "typescript":
                return (True, "Installed typescript")
            else:
                return (False, "Package not found")

        mock_client.install_single = AsyncMock(side_effect=install_side_effect)

        installer = NpmInstaller(client=mock_client)
        results = await installer._install_sequential(["typescript", "nonexistent"])

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    @pytest.mark.asyncio
    async def test_install_sequential_with_progress(self) -> None:
        """Test _install_sequential calls progress callback."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(return_value=(True, "Installed"))

        progress_calls = []

        def on_progress(pkg: str, status: str) -> None:
            progress_calls.append((pkg, status))

        installer = NpmInstaller(client=mock_client)
        await installer._install_sequential(["typescript"], on_progress=on_progress)

        assert len(progress_calls) == 2
        assert ("typescript", "Installing...") in progress_calls
        assert ("typescript", "✓ Installed") in progress_calls

    @pytest.mark.asyncio
    async def test_install_sequential_exception_handling(self) -> None:
        """Test _install_sequential handles exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(side_effect=Exception("Connection timeout"))

        installer = NpmInstaller(client=mock_client)
        results = await installer._install_sequential(["typescript"])

        assert len(results) == 1
        assert results[0].success is False
        assert "Connection timeout" in results[0].message

    @pytest.mark.asyncio
    async def test_install_single_success(self) -> None:
        """Test install_single successfully installs a package."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(return_value=(True, "added typescript@5.0.0"))

        installer = NpmInstaller(client=mock_client)
        result = await installer.install_single("typescript")

        assert result.success is True
        assert result.package == "typescript"
        assert result.already_installed is False
        assert result.batch is False
        mock_client.install_single.assert_called_once_with("typescript", timeout=300.0)

    @pytest.mark.asyncio
    async def test_install_single_already_installed(self) -> None:
        """Test install_single detects already installed packages."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(return_value=(True, "typescript is already installed"))

        installer = NpmInstaller(client=mock_client)
        result = await installer.install_single("typescript")

        assert result.success is True
        assert result.already_installed is True

    @pytest.mark.asyncio
    async def test_install_single_failure(self) -> None:
        """Test install_single handles installation failure."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(return_value=(False, "Package not found"))

        installer = NpmInstaller(client=mock_client)
        result = await installer.install_single("nonexistent")

        assert result.success is False
        assert result.package == "nonexistent"
        assert "Package not found" in result.message

    @pytest.mark.asyncio
    async def test_install_single_with_progress(self) -> None:
        """Test install_single calls progress callback."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(return_value=(True, "added typescript@5.0.0"))

        progress_calls = []

        def on_progress(pkg: str, status: str) -> None:
            progress_calls.append((pkg, status))

        installer = NpmInstaller(client=mock_client)
        await installer.install_single("typescript", on_progress=on_progress)

        assert len(progress_calls) == 2
        assert ("typescript", "Installing...") in progress_calls
        assert ("typescript", "✓ Installed") in progress_calls

    @pytest.mark.asyncio
    async def test_install_single_exception(self) -> None:
        """Test install_single handles exceptions."""
        mock_client = MagicMock()
        mock_client.install_single = AsyncMock(side_effect=Exception("Connection timeout"))

        installer = NpmInstaller(client=mock_client)
        result = await installer.install_single("typescript")

        assert result.success is False
        assert "Connection timeout" in result.message

    @pytest.mark.asyncio
    async def test_batch_retry_exponential_backoff(self) -> None:
        """Test batch install uses exponential backoff on retries."""
        mock_client = MagicMock()
        mock_client.install_global = AsyncMock(return_value=(False, "Network error"))
        mock_client.install_single = AsyncMock(return_value=(True, "Installed"))

        start_time = asyncio.get_event_loop().time()

        installer = NpmInstaller(client=mock_client, max_retries=3)
        await installer.install_packages(["typescript"])

        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time

        # Should have waited: 2^1 + 2^2 + 2^3 = 2 + 4 + 8 = 14 seconds for batch retries
        # But since we have max_retries=3, it's 2^1 + 2^2 = 6 seconds
        # Allow tolerance for execution time
        assert elapsed >= 5.5
        assert elapsed < 7.5

    @pytest.mark.asyncio
    async def test_batch_with_progress_retry_messages(self) -> None:
        """Test batch install shows retry progress messages."""
        mock_client = MagicMock()
        mock_client.install_global = AsyncMock(
            side_effect=[
                (False, "Network error"),
                (True, "added 1 package"),
            ]
        )

        progress_calls = []

        def on_progress(pkg: str, status: str) -> None:
            progress_calls.append((pkg, status))

        installer = NpmInstaller(client=mock_client, max_retries=3)
        await installer.install_packages(["typescript"], on_progress=on_progress)

        # Should have retry message
        retry_messages = [call for call in progress_calls if "retrying" in call[1]]
        assert len(retry_messages) >= 1
        assert "npm" in retry_messages[0][0]
