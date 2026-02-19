"""Unit tests for BrewInstaller dry-run functionality."""

import pytest

from pysetitup.brew.installer import BrewInstaller


class TestBrewInstallerDryRun:
    """Test dry-run functionality for BrewInstaller."""

    @pytest.mark.asyncio
    async def test_install_formula_dry_run(self) -> None:
        """Test install_formula in dry-run mode."""
        installer = BrewInstaller()

        result = await installer.install_formula("git", dry_run=True)

        assert result.success is True
        assert result.package == "git"
        assert "Dry run" in result.message
        assert result.attempts == 0

    @pytest.mark.asyncio
    async def test_install_cask_dry_run(self) -> None:
        """Test install_cask in dry-run mode."""
        installer = BrewInstaller()

        result = await installer.install_cask("visual-studio-code", dry_run=True)

        assert result.success is True
        assert result.package == "visual-studio-code"
        assert "Dry run" in result.message
        assert result.attempts == 0

    @pytest.mark.asyncio
    async def test_install_packages_dry_run(self) -> None:
        """Test install_packages in dry-run mode."""
        installer = BrewInstaller()

        results = await installer.install_packages(
            formulae=["git", "fzf"],
            casks=["warp", "rectangle"],
            dry_run=True
        )

        assert len(results) == 4
        assert all(r.success for r in results)
        assert all("Dry run" in r.message for r in results)
        assert all(r.attempts == 0 for r in results)

    @pytest.mark.asyncio
    async def test_tap_repositories_dry_run(self) -> None:
        """Test tap_repositories in dry-run mode."""
        installer = BrewInstaller()

        results = await installer.tap_repositories(
            taps=["homebrew/cask-fonts", "homebrew/cask-versions"],
            dry_run=True
        )

        assert len(results) == 2
        assert all(r.success for r in results)
        assert all("Dry run" in r.message for r in results)

    @pytest.mark.asyncio
    async def test_dry_run_with_progress_callback(self) -> None:
        """Test dry-run mode with progress callback."""
        installer = BrewInstaller()
        progress_calls = []

        def on_progress(package: str, status: str) -> None:
            progress_calls.append((package, status))

        await installer.install_formula("git", on_progress=on_progress, dry_run=True)

        assert len(progress_calls) == 1
        assert progress_calls[0][0] == "git"
        assert "[DRY RUN]" in progress_calls[0][1]

    @pytest.mark.asyncio
    async def test_dry_run_no_actual_installation(self) -> None:
        """Test that dry-run doesn't call actual install methods."""
        from unittest.mock import AsyncMock

        installer = BrewInstaller()
        installer.client.install_formula = AsyncMock()

        await installer.install_formula("git", dry_run=True)

        # Should not call the actual install method
        installer.client.install_formula.assert_not_called()
