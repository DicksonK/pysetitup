"""Async parallel Homebrew package installer."""

import asyncio
from collections.abc import Awaitable, Callable

from pysetitup.brew.client import BrewClient
from pysetitup.installer.models import BrewInstallResult as InstallResult


class BrewInstaller:
    """Async parallel Homebrew package installer with retry logic."""

    def __init__(
        self,
        client: BrewClient | None = None,
        max_concurrent: int = 5,
        max_retries: int = 3,
    ):
        """
        Initialize BrewInstaller.

        Args:
            client: BrewClient instance (creates new one if None)
            max_concurrent: Maximum number of concurrent installations (must be > 0)
            max_retries: Maximum retry attempts per package (must be >= 0)

        Raises:
            ValueError: If max_concurrent <= 0 or max_retries < 0
        """
        if max_concurrent <= 0:
            raise ValueError(f"max_concurrent must be > 0, got {max_concurrent}")
        if max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {max_retries}")

        self.client = client or BrewClient()
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _install_with_retry(
        self,
        package: str,
        install_func: Callable[[str], Awaitable[tuple[bool, str]]],
        package_type: str,
        on_progress: Callable[[str, str], None] | None = None,
        dry_run: bool = False,
    ) -> InstallResult:
        """
        Install a package with retry logic (generic method).

        Args:
            package: Package name
            install_func: Async function to call for installation
            package_type: Type of package ("formula" or "cask") for messages
            on_progress: Optional callback(package_name, status) for progress updates
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
                message=f"Dry run - would install {package_type}",
                attempts=0,
            )

        async with self._semaphore:
            for attempt in range(1, self.max_retries + 1):
                try:
                    if on_progress:
                        on_progress(
                            package,
                            f"Installing... (attempt {attempt}/{self.max_retries})",
                        )

                    success, message = await install_func(package)

                    # Check if already installed
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
                            attempts=attempt,
                        )

                    # Installation failed, check if already installed
                    if already_installed:
                        if on_progress:
                            on_progress(package, "✓ Already installed")

                        return InstallResult(
                            package=package,
                            success=True,
                            message=message,
                            already_installed=True,
                            attempts=attempt,
                        )

                    # Installation failed, retry if we have attempts left
                    if attempt < self.max_retries:
                        backoff = 2**attempt  # Exponential backoff
                        if on_progress:
                            on_progress(package, f"⚠ Failed, retrying in {backoff}s...")
                        await asyncio.sleep(backoff)
                    else:
                        # Final attempt failed
                        if on_progress:
                            on_progress(package, "✗ Failed")

                        return InstallResult(
                            package=package,
                            success=False,
                            message=message,
                            attempts=attempt,
                        )

                except Exception as e:
                    if attempt < self.max_retries:
                        backoff = 2**attempt
                        if on_progress:
                            on_progress(package, f"⚠ Error, retrying in {backoff}s...")
                        await asyncio.sleep(backoff)
                    else:
                        if on_progress:
                            on_progress(package, "✗ Error")

                        return InstallResult(
                            package=package,
                            success=False,
                            message=str(e),
                            attempts=attempt,
                        )

            # Should never reach here, but just in case
            return InstallResult(
                package=package,
                success=False,
                message="Unknown error",
                attempts=self.max_retries,
            )

    async def install_formula(
        self,
        package: str,
        on_progress: Callable[[str, str], None] | None = None,
        dry_run: bool = False,
    ) -> InstallResult:
        """
        Install a single formula with retry logic.

        Args:
            package: Package name
            on_progress: Optional callback(package_name, status) for progress updates
            dry_run: If True, simulate installation without actually installing

        Returns:
            InstallResult with installation details
        """
        return await self._install_with_retry(
            package,
            self.client.install_formula,
            "formula",
            on_progress,
            dry_run,
        )

    async def install_cask(
        self,
        package: str,
        on_progress: Callable[[str, str], None] | None = None,
        dry_run: bool = False,
    ) -> InstallResult:
        """
        Install a single cask with retry logic.

        Args:
            package: Cask name
            on_progress: Optional callback(package_name, status) for progress updates
            dry_run: If True, simulate installation without actually installing

        Returns:
            InstallResult with installation details
        """
        return await self._install_with_retry(
            package,
            self.client.install_cask,
            "cask",
            on_progress,
            dry_run,
        )

    async def install_packages(
        self,
        formulae: list[str],
        casks: list[str],
        on_progress: Callable[[str, str], None] | None = None,
        dry_run: bool = False,
    ) -> list[InstallResult]:
        """
        Install multiple packages in parallel.

        Args:
            formulae: List of formula names to install
            casks: List of cask names to install
            on_progress: Optional callback(package_name, status) for progress updates
            dry_run: If True, simulate installation without actually installing

        Returns:
            List of InstallResult for all packages
        """
        # Create tasks for all packages
        formula_tasks = [self.install_formula(pkg, on_progress, dry_run) for pkg in formulae]
        cask_tasks = [self.install_cask(pkg, on_progress, dry_run) for pkg in casks]

        # Run all tasks in parallel (limited by semaphore)
        all_tasks = formula_tasks + cask_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Convert exceptions to InstallResult
        final_results = []
        all_packages = formulae + casks

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(
                    InstallResult(
                        package=all_packages[i],
                        success=False,
                        message=str(result),
                        attempts=1,
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def tap_repositories(
        self,
        taps: list[str],
        on_progress: Callable[[str, str], None] | None = None,
        dry_run: bool = False,
    ) -> list[InstallResult]:
        """
        Tap multiple repositories.

        Args:
            taps: List of tap names (e.g., ["homebrew/cask-fonts"])
            on_progress: Optional callback(tap_name, status) for progress updates
            dry_run: If True, simulate tapping without actually tapping

        Returns:
            List of InstallResult for all taps
        """
        results = []

        for tap in taps:
            try:
                if dry_run:
                    if on_progress:
                        on_progress(tap, "[DRY RUN] Would tap")
                    results.append(
                        InstallResult(
                            package=tap,
                            success=True,
                            message="Dry run - would tap repository",
                            attempts=0,
                        )
                    )
                    continue

                if on_progress:
                    on_progress(tap, "Tapping...")

                success, message = await self.client.tap(tap)

                if on_progress:
                    on_progress(tap, "✓ Tapped" if success else "✗ Failed")

                results.append(
                    InstallResult(
                        package=tap,
                        success=success,
                        message=message,
                        attempts=1,
                    )
                )

            except Exception as e:
                if on_progress:
                    on_progress(tap, "✗ Error")

                results.append(
                    InstallResult(
                        package=tap,
                        success=False,
                        message=str(e),
                        attempts=1,
                    )
                )

        return results
