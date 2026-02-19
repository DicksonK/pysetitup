"""Unit tests for NpmInstaller dry-run functionality."""

import pytest

from pysetitup.npm.installer import NpmInstaller


class TestNpmInstallerDryRun:
    """Test dry-run functionality for NpmInstaller."""

    @pytest.mark.asyncio
    async def test_install_packages_dry_run(self) -> None:
        """Test install_packages in dry-run mode."""
        installer = NpmInstaller()

        results = await installer.install_packages(packages=["typescript", "eslint", "prettier"], dry_run=True)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert all("Dry run" in r.message for r in results)
        assert all(r.already_installed is False for r in results)

    @pytest.mark.asyncio
    async def test_install_single_dry_run(self) -> None:
        """Test install_single in dry-run mode."""
        installer = NpmInstaller()

        result = await installer.install_single("typescript", dry_run=True)

        assert result.success is True
        assert result.package == "typescript"
        assert "Dry run" in result.message
        assert result.already_installed is False
        assert result.batch is False

    @pytest.mark.asyncio
    async def test_dry_run_with_progress_callback(self) -> None:
        """Test dry-run mode with progress callback."""
        installer = NpmInstaller()
        progress_calls = []

        def on_progress(package: str, status: str) -> None:
            progress_calls.append((package, status))

        await installer.install_packages(packages=["typescript", "eslint"], on_progress=on_progress, dry_run=True)

        assert len(progress_calls) == 1
        assert "[DRY RUN]" in progress_calls[0][1]

    @pytest.mark.asyncio
    async def test_dry_run_no_actual_installation(self) -> None:
        """Test that dry-run doesn't call actual install methods."""
        from unittest.mock import AsyncMock

        installer = NpmInstaller()
        installer.client.install_global = AsyncMock()
        installer.client.install_single = AsyncMock()

        await installer.install_packages(["typescript"], dry_run=True)

        # Should not call actual install methods
        installer.client.install_global.assert_not_called()
        installer.client.install_single.assert_not_called()

    @pytest.mark.asyncio
    async def test_dry_run_empty_package_list(self) -> None:
        """Test dry-run with empty package list."""
        installer = NpmInstaller()

        results = await installer.install_packages(packages=[], dry_run=True)

        assert results == []
