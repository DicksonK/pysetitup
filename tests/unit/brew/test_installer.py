"""Unit tests for pysetitup.brew.installer module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pysetitup.brew.installer import BrewInstaller, InstallResult


class TestBrewInstaller:
    """Test the BrewInstaller class."""

    @pytest.mark.asyncio
    async def test_install_formula_success(self) -> None:
        """Test install_formula successfully installs a package."""
        mock_client = MagicMock()
        mock_client.install_formula = AsyncMock(return_value=(True, "Installed git"))

        installer = BrewInstaller(client=mock_client)
        result = await installer.install_formula("git")

        assert result.success is True
        assert result.package == "git"
        assert result.attempts == 1
        assert result.already_installed is False
        mock_client.install_formula.assert_called_once_with("git")

    @pytest.mark.asyncio
    async def test_install_formula_already_installed(self) -> None:
        """Test install_formula detects already installed packages."""
        mock_client = MagicMock()
        mock_client.install_formula = AsyncMock(
            return_value=(True, "git is already installed")
        )

        installer = BrewInstaller(client=mock_client)
        result = await installer.install_formula("git")

        assert result.success is True
        assert result.already_installed is True

    @pytest.mark.asyncio
    async def test_install_formula_retry_success(self) -> None:
        """Test install_formula retries and succeeds on 2nd attempt."""
        mock_client = MagicMock()
        # First call fails, second succeeds
        mock_client.install_formula = AsyncMock(
            side_effect=[
                (False, "Network error"),
                (True, "Installed git"),
            ]
        )

        installer = BrewInstaller(client=mock_client, max_retries=3)
        result = await installer.install_formula("git")

        assert result.success is True
        assert result.attempts == 2
        assert mock_client.install_formula.call_count == 2

    @pytest.mark.asyncio
    async def test_install_formula_retry_exhausted(self) -> None:
        """Test install_formula fails after max retries."""
        mock_client = MagicMock()
        mock_client.install_formula = AsyncMock(
            return_value=(False, "Network error")
        )

        installer = BrewInstaller(client=mock_client, max_retries=2)
        result = await installer.install_formula("git")

        assert result.success is False
        assert result.attempts == 2
        assert mock_client.install_formula.call_count == 2

    @pytest.mark.asyncio
    async def test_install_formula_with_progress_callback(self) -> None:
        """Test install_formula calls progress callback."""
        mock_client = MagicMock()
        mock_client.install_formula = AsyncMock(return_value=(True, "Installed git"))

        progress_calls = []

        def on_progress(pkg: str, status: str) -> None:
            progress_calls.append((pkg, status))

        installer = BrewInstaller(client=mock_client)
        await installer.install_formula("git", on_progress=on_progress)

        assert len(progress_calls) == 2
        assert progress_calls[0] == ("git", "Installing... (attempt 1/3)")
        assert progress_calls[1] == ("git", "✓ Installed")

    @pytest.mark.asyncio
    async def test_install_formula_exception_retry(self) -> None:
        """Test install_formula retries on exception."""
        mock_client = MagicMock()
        # First call raises exception, second succeeds
        mock_client.install_formula = AsyncMock(
            side_effect=[
                Exception("Connection timeout"),
                (True, "Installed git"),
            ]
        )

        installer = BrewInstaller(client=mock_client, max_retries=3)
        result = await installer.install_formula("git")

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_install_cask_success(self) -> None:
        """Test install_cask successfully installs a cask."""
        mock_client = MagicMock()
        mock_client.install_cask = AsyncMock(return_value=(True, "Installed docker"))

        installer = BrewInstaller(client=mock_client)
        result = await installer.install_cask("docker")

        assert result.success is True
        assert result.package == "docker"
        assert result.attempts == 1
        mock_client.install_cask.assert_called_once_with("docker")

    @pytest.mark.asyncio
    async def test_install_cask_retry(self) -> None:
        """Test install_cask retries on failure."""
        mock_client = MagicMock()
        mock_client.install_cask = AsyncMock(
            side_effect=[
                (False, "Download failed"),
                (True, "Installed docker"),
            ]
        )

        installer = BrewInstaller(client=mock_client, max_retries=3)
        result = await installer.install_cask("docker")

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_install_packages_parallel(self) -> None:
        """Test install_packages installs multiple packages in parallel."""
        mock_client = MagicMock()
        mock_client.install_formula = AsyncMock(return_value=(True, "Installed"))
        mock_client.install_cask = AsyncMock(return_value=(True, "Installed"))

        installer = BrewInstaller(client=mock_client, max_concurrent=5)
        results = await installer.install_packages(
            formulae=["git", "node"], casks=["docker", "vscode"]
        )

        assert len(results) == 4
        assert all(r.success for r in results)
        assert mock_client.install_formula.call_count == 2
        assert mock_client.install_cask.call_count == 2

    @pytest.mark.asyncio
    async def test_install_packages_mixed_results(self) -> None:
        """Test install_packages handles mixed success/failure."""
        mock_client = MagicMock()

        async def install_formula_side_effect(pkg):
            if pkg == "git":
                return (True, "Installed git")
            else:
                return (False, "Package not found")

        mock_client.install_formula = AsyncMock(side_effect=install_formula_side_effect)
        mock_client.install_cask = AsyncMock(return_value=(True, "Installed"))

        installer = BrewInstaller(client=mock_client, max_concurrent=5)
        results = await installer.install_packages(
            formulae=["git", "nonexistent"], casks=["docker"]
        )

        assert len(results) == 3
        assert results[0].success is True  # git
        assert results[1].success is False  # nonexistent
        assert results[2].success is True  # docker

    @pytest.mark.asyncio
    async def test_install_packages_with_progress(self) -> None:
        """Test install_packages with progress callback."""
        mock_client = MagicMock()
        mock_client.install_formula = AsyncMock(return_value=(True, "Installed"))
        mock_client.install_cask = AsyncMock(return_value=(True, "Installed"))

        progress_calls = []

        def on_progress(pkg: str, status: str) -> None:
            progress_calls.append((pkg, status))

        installer = BrewInstaller(client=mock_client)
        await installer.install_packages(
            formulae=["git"], casks=["docker"], on_progress=on_progress
        )

        # Should have progress calls for both packages
        assert len(progress_calls) > 0
        package_names = {call[0] for call in progress_calls}
        assert "git" in package_names
        assert "docker" in package_names

    @pytest.mark.asyncio
    async def test_install_packages_concurrency_limit(self) -> None:
        """Test install_packages respects max_concurrent limit."""
        mock_client = MagicMock()

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent_seen = 0

        async def install_formula_with_delay(pkg):
            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            await asyncio.sleep(0.01)  # Simulate work
            concurrent_count -= 1
            return (True, f"Installed {pkg}")

        mock_client.install_formula = AsyncMock(side_effect=install_formula_with_delay)
        mock_client.install_cask = AsyncMock(return_value=(True, "Installed"))

        installer = BrewInstaller(client=mock_client, max_concurrent=2)
        await installer.install_packages(
            formulae=["pkg1", "pkg2", "pkg3", "pkg4"], casks=[]
        )

        # Max concurrent should not exceed limit
        assert max_concurrent_seen <= 2

    @pytest.mark.asyncio
    async def test_tap_repositories_success(self) -> None:
        """Test tap_repositories successfully taps repos."""
        mock_client = MagicMock()
        mock_client.tap = AsyncMock(return_value=(True, "Tapped homebrew/cask"))

        installer = BrewInstaller(client=mock_client)
        results = await installer.tap_repositories(["homebrew/cask", "custom/tap"])

        assert len(results) == 2
        assert all(r.success for r in results)
        assert mock_client.tap.call_count == 2

    @pytest.mark.asyncio
    async def test_tap_repositories_with_failures(self) -> None:
        """Test tap_repositories handles failures."""
        mock_client = MagicMock()

        async def tap_side_effect(name):
            if name == "homebrew/cask":
                return (True, "Tapped")
            else:
                return (False, "Tap not found")

        mock_client.tap = AsyncMock(side_effect=tap_side_effect)

        installer = BrewInstaller(client=mock_client)
        results = await installer.tap_repositories(
            ["homebrew/cask", "invalid/tap"]
        )

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    @pytest.mark.asyncio
    async def test_tap_repositories_with_progress(self) -> None:
        """Test tap_repositories with progress callback."""
        mock_client = MagicMock()
        mock_client.tap = AsyncMock(return_value=(True, "Tapped"))

        progress_calls = []

        def on_progress(tap: str, status: str) -> None:
            progress_calls.append((tap, status))

        installer = BrewInstaller(client=mock_client)
        await installer.tap_repositories(
            ["homebrew/cask"], on_progress=on_progress
        )

        assert len(progress_calls) == 2
        assert progress_calls[0] == ("homebrew/cask", "Tapping...")
        assert progress_calls[1] == ("homebrew/cask", "✓ Tapped")

    @pytest.mark.asyncio
    async def test_exponential_backoff(self) -> None:
        """Test retry uses exponential backoff."""
        mock_client = MagicMock()
        mock_client.install_formula = AsyncMock(
            return_value=(False, "Network error")
        )

        start_time = asyncio.get_event_loop().time()

        installer = BrewInstaller(client=mock_client, max_retries=3)
        await installer.install_formula("git")

        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time

        # Should have waited: 2^1 + 2^2 = 2 + 4 = 6 seconds
        # Allow some tolerance for execution time
        assert elapsed >= 5.5
        assert elapsed < 7.0
