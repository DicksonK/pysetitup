"""npm package installer with batch install and fallback."""

import asyncio
from typing import Callable, Optional

from pysetitup.installer.models import NpmInstallResult as InstallResult
from pysetitup.npm.client import NpmClient
from pysetitup.npm.parser import NpmParser
from pysetitup.utils.errors import InstallationError


class NpmInstaller:
    """npm package installer with batch install and sequential fallback."""

    def __init__(
        self,
        client: Optional[NpmClient] = None,
        max_retries: int = 2,
    ):
        """
        Initialize NpmInstaller.

        Args:
            client: NpmClient instance (creates new one if None)
            max_retries: Maximum retry attempts for batch install (must be >= 0)

        Raises:
            ValueError: If max_retries < 0
        """
        if max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {max_retries}")

        self.client = client or NpmClient()
        self.max_retries = max_retries

    async def install_packages(
        self,
        packages: list[str],
        on_progress: Optional[Callable[[str, str], None]] = None,
        dry_run: bool = False,
    ) -> list[InstallResult]:
        """
        Install multiple npm packages.

        Strategy:
        1. Try batch install first (npm install -g pkg1 pkg2 pkg3)
        2. If batch fails, fall back to sequential installation

        Args:
            packages: List of package names to install
            on_progress: Optional callback(package_name, status) for progress updates
            dry_run: If True, simulate installation without actually installing

        Returns:
            List of InstallResult for all packages
        """
        if not packages:
            return []

        if dry_run:
            if on_progress:
                on_progress("npm", f"[DRY RUN] Would install {len(packages)} packages")
            return [
                InstallResult(
                    package=pkg,
                    success=True,
                    message="Dry run - would install package",
                    already_installed=False,
                )
                for pkg in packages
            ]

        # Try batch install first
        if on_progress:
            on_progress("npm", f"Installing {len(packages)} packages (batch)...")

        for attempt in range(1, self.max_retries + 1):
            try:
                success, message = await self.client.install_global(
                    packages, timeout=600.0
                )

                if success:
                    if on_progress:
                        on_progress("npm", f"✓ Installed {len(packages)} packages")

                    # Return success for all packages
                    return [
                        InstallResult(
                            package=pkg,
                            success=True,
                            message=f"Installed via batch ({len(packages)} total)",
                            batch=True,
                        )
                        for pkg in packages
                    ]

                # Batch failed, retry if we have attempts left
                if attempt < self.max_retries:
                    backoff = 2**attempt
                    if on_progress:
                        on_progress(
                            "npm", f"⚠ Batch install failed, retrying in {backoff}s..."
                        )
                    await asyncio.sleep(backoff)

            except Exception as e:
                if attempt < self.max_retries:
                    backoff = 2**attempt
                    if on_progress:
                        on_progress(
                            "npm", f"⚠ Error in batch install, retrying in {backoff}s..."
                        )
                    await asyncio.sleep(backoff)

        # Batch install failed, fall back to sequential
        if on_progress:
            on_progress("npm", "Batch failed, installing sequentially...")

        return await self._install_sequential(packages, on_progress)

    async def _install_sequential(
        self,
        packages: list[str],
        on_progress: Optional[Callable[[str, str], None]] = None,
    ) -> list[InstallResult]:
        """
        Install packages one by one (fallback strategy).

        Args:
            packages: List of package names
            on_progress: Optional progress callback

        Returns:
            List of InstallResult for all packages
        """
        results = []

        for pkg in packages:
            try:
                if on_progress:
                    on_progress(pkg, "Installing...")

                success, message = await self.client.install_single(pkg, timeout=300.0)

                # Check if already installed
                already_installed = "already installed" in message.lower()

                if success:
                    if on_progress:
                        status = (
                            "✓ Already installed" if already_installed else "✓ Installed"
                        )
                        on_progress(pkg, status)

                    results.append(
                        InstallResult(
                            package=pkg,
                            success=True,
                            message=message,
                            already_installed=already_installed,
                            batch=False,
                        )
                    )
                else:
                    if on_progress:
                        on_progress(pkg, "✗ Failed")

                    results.append(
                        InstallResult(
                            package=pkg,
                            success=False,
                            message=message,
                            batch=False,
                        )
                    )

            except Exception as e:
                if on_progress:
                    on_progress(pkg, "✗ Error")

                results.append(
                    InstallResult(
                        package=pkg,
                        success=False,
                        message=str(e),
                        batch=False,
                    )
                )

        return results

    async def install_single(
        self,
        package: str,
        on_progress: Optional[Callable[[str, str], None]] = None,
        dry_run: bool = False,
    ) -> InstallResult:
        """
        Install a single npm package.

        Args:
            package: Package name
            on_progress: Optional progress callback
            dry_run: If True, simulate installation without actually installing

        Returns:
            InstallResult with installation details
        """
        if dry_run:
            if on_progress:
                on_progress(package, "[DRY RUN] Would install")
            return InstallResult(
                package=package,
                success=True,
                message="Dry run - would install package",
                already_installed=False,
                batch=False,
            )

        try:
            if on_progress:
                on_progress(package, "Installing...")

            success, message = await self.client.install_single(package, timeout=300.0)

            already_installed = "already installed" in message.lower()

            if success:
                if on_progress:
                    status = "✓ Already installed" if already_installed else "✓ Installed"
                    on_progress(package, status)

                return InstallResult(
                    package=package,
                    success=True,
                    message=message,
                    already_installed=already_installed,
                    batch=False,
                )
            else:
                if on_progress:
                    on_progress(package, "✗ Failed")

                return InstallResult(
                    package=package,
                    success=False,
                    message=message,
                    batch=False,
                )

        except Exception as e:
            if on_progress:
                on_progress(package, "✗ Error")

            return InstallResult(
                package=package,
                success=False,
                message=str(e),
                batch=False,
            )
