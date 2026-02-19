"""VS Code extension installer with parallel installation support."""

import asyncio
from typing import Callable, Optional

from pysetitup.installer.models import VSCodeInstallResult as InstallResult
from pysetitup.vscode.client import VSCodeClient


class VSCodeInstaller:
    """Installer for VS Code extensions with parallel installation."""

    def __init__(
        self,
        client: Optional[VSCodeClient] = None,
        max_concurrent: int = 3,
    ) -> None:
        """
        Initialize VS Code extension installer.

        Args:
            client: VS Code client to use (creates default if None)
            max_concurrent: Maximum number of concurrent installations (must be > 0)

        Raises:
            ValueError: If max_concurrent <= 0
        """
        if max_concurrent <= 0:
            raise ValueError(f"max_concurrent must be > 0, got {max_concurrent}")

        self.client = client or VSCodeClient()
        self.max_concurrent = max_concurrent

    async def install_extensions(
        self,
        extension_ids: list[str],
        on_progress: Optional[Callable[[str], None]] = None,
        dry_run: bool = False,
    ) -> list[InstallResult]:
        """
        Install VS Code extensions in parallel.

        Args:
            extension_ids: List of extension IDs to install
            on_progress: Optional callback for progress updates
            dry_run: If True, only simulate installation

        Returns:
            List of InstallResult objects
        """
        if dry_run:
            if on_progress:
                on_progress(f"[DRY RUN] Would install {len(extension_ids)} extensions")
            return [
                InstallResult(
                    extension_id=ext_id,
                    success=True,
                    already_installed=False,
                )
                for ext_id in extension_ids
            ]

        # Check if VS Code CLI is available
        if not await self.client.is_installed():
            if on_progress:
                on_progress("VS Code CLI not available - skipping extension installation")
            return [
                InstallResult(
                    extension_id=ext_id,
                    success=False,
                    error="VS Code CLI not available",
                )
                for ext_id in extension_ids
            ]

        # Get currently installed extensions
        try:
            installed = await self.client.list_extensions_with_versions()
        except Exception:
            installed = {}

        results = []
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def install_one(extension_id: str) -> InstallResult:
            """Install a single extension with concurrency control."""
            async with semaphore:
                # Check if already installed
                if extension_id in installed:
                    if on_progress:
                        on_progress(f"✓ {extension_id} (already installed)")
                    return InstallResult(
                        extension_id=extension_id,
                        success=True,
                        already_installed=True,
                        version=installed.get(extension_id),
                    )

                # Install the extension
                if on_progress:
                    on_progress(f"Installing {extension_id}...")

                try:
                    success, message = await self.client.install_extension(extension_id)

                    if success:
                        if on_progress:
                            on_progress(f"✓ {extension_id}")
                        return InstallResult(
                            extension_id=extension_id,
                            success=True,
                            already_installed="already installed" in message.lower(),
                        )
                    else:
                        if on_progress:
                            on_progress(f"✗ {extension_id}: {message}")
                        return InstallResult(
                            extension_id=extension_id,
                            success=False,
                            error=message,
                        )
                except Exception as e:
                    error_msg = str(e)
                    if on_progress:
                        on_progress(f"✗ {extension_id}: {error_msg}")
                    return InstallResult(
                        extension_id=extension_id,
                        success=False,
                        error=error_msg,
                    )

        # Install all extensions in parallel
        tasks = [install_one(ext_id) for ext_id in extension_ids]
        results = await asyncio.gather(*tasks)

        return list(results)

    async def uninstall_extensions(
        self,
        extension_ids: list[str],
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> list[InstallResult]:
        """
        Uninstall VS Code extensions.

        Args:
            extension_ids: List of extension IDs to uninstall
            on_progress: Optional callback for progress updates

        Returns:
            List of InstallResult objects
        """
        results = []

        for extension_id in extension_ids:
            if on_progress:
                on_progress(f"Uninstalling {extension_id}...")

            success, message = await self.client.uninstall_extension(extension_id)

            if success:
                if on_progress:
                    on_progress(f"✓ Uninstalled {extension_id}")
            else:
                if on_progress:
                    on_progress(f"✗ Failed to uninstall {extension_id}: {message}")

            results.append(
                InstallResult(
                    extension_id=extension_id,
                    success=success,
                    error=None if success else message,
                )
            )

        return results
