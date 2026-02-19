"""Homebrew command execution client."""

import asyncio
import shutil

from pysetitup.utils.errors import DependencyError, InstallationError


class BrewClient:
    """Client for executing Homebrew commands."""

    def __init__(self, brew_path: str | None = None):
        """
        Initialize BrewClient.

        Args:
            brew_path: Optional path to brew executable (auto-detected if None)

        Raises:
            DependencyError: If Homebrew is not installed
        """
        self.brew_path = brew_path or self._find_brew()
        if not self.brew_path:
            raise DependencyError("Homebrew is not installed. Install from https://brew.sh")

    def _find_brew(self) -> str | None:
        """
        Find the brew executable in PATH.

        Returns:
            Path to brew executable or None if not found
        """
        return shutil.which("brew")

    async def _run_command(
        self,
        args: list[str],
        check: bool = True,
        timeout: float | None = None,
    ) -> tuple[int, str, str]:
        """
        Run a brew command asynchronously.

        Args:
            args: Command arguments (brew is prepended automatically)
            check: If True, raise error on non-zero exit code
            timeout: Optional timeout in seconds

        Returns:
            Tuple of (returncode, stdout, stderr)

        Raises:
            InstallationError: If command fails and check=True
            asyncio.TimeoutError: If command times out
        """
        cmd = [self.brew_path] + args

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            returncode = proc.returncode or 0

            if check and returncode != 0:
                # Extract package name from args if possible
                pkg_name = args[1] if len(args) > 1 else "unknown"
                raise InstallationError(
                    package=pkg_name,
                    message=f"Brew command failed: {' '.join(args)}\n" f"Exit code: {returncode}\n" f"Stderr: {stderr}",
                )

            return returncode, stdout, stderr

        except asyncio.TimeoutError:
            # Kill the process if it times out
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
            raise

    async def install_formula(self, name: str, timeout: float | None = 600.0) -> tuple[bool, str]:
        """
        Install a Homebrew formula.

        Args:
            name: Formula name
            timeout: Timeout in seconds (default: 600s = 10 minutes)

        Returns:
            Tuple of (success, message)
        """
        try:
            _, stdout, stderr = await self._run_command(["install", name], check=True, timeout=timeout)
            return True, f"Installed {name}"
        except InstallationError as e:
            return False, str(e)
        except asyncio.TimeoutError:
            return False, f"Installation of {name} timed out after {timeout}s"

    async def install_cask(self, name: str, timeout: float | None = 600.0) -> tuple[bool, str]:
        """
        Install a Homebrew cask.

        Args:
            name: Cask name
            timeout: Timeout in seconds (default: 600s = 10 minutes)

        Returns:
            Tuple of (success, message)
        """
        try:
            _, stdout, stderr = await self._run_command(["install", "--cask", name], check=True, timeout=timeout)
            return True, f"Installed {name}"
        except InstallationError as e:
            return False, str(e)
        except asyncio.TimeoutError:
            return False, f"Installation of {name} timed out after {timeout}s"

    async def tap(self, name: str) -> tuple[bool, str]:
        """
        Tap a Homebrew repository.

        Args:
            name: Tap name (e.g., "homebrew/cask-fonts")

        Returns:
            Tuple of (success, message)
        """
        try:
            _, stdout, stderr = await self._run_command(["tap", name], check=True)
            return True, f"Tapped {name}"
        except InstallationError as e:
            return False, str(e)

    async def list_formulae(self) -> list[str]:
        """
        List installed formulae.

        Returns:
            List of installed formula names
        """
        try:
            _, stdout, _ = await self._run_command(["list", "--formula"], check=True)
            return [line.strip() for line in stdout.strip().split("\n") if line.strip()]
        except InstallationError:
            return []

    async def list_formulae_versions(self) -> dict[str, str]:
        """
        List installed formulae with versions.

        Returns:
            Dictionary mapping package name to version
        """
        try:
            _, stdout, _ = await self._run_command(["list", "--formula", "--versions"], check=True)
            versions = {}
            for line in stdout.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        versions[name] = version
            return versions
        except InstallationError:
            return {}

    async def list_casks(self) -> list[str]:
        """
        List installed casks.

        Returns:
            List of installed cask names
        """
        try:
            _, stdout, _ = await self._run_command(["list", "--cask"], check=True)
            return [line.strip() for line in stdout.strip().split("\n") if line.strip()]
        except InstallationError:
            return []

    async def list_casks_versions(self) -> dict[str, str]:
        """
        List installed casks with versions.

        Returns:
            Dictionary mapping package name to version
        """
        try:
            _, stdout, _ = await self._run_command(["list", "--cask", "--versions"], check=True)
            versions = {}
            for line in stdout.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        versions[name] = version
            return versions
        except InstallationError:
            return {}

    async def info(self, name: str, cask: bool = False) -> dict[str, str] | None:
        """
        Get information about a package.

        Args:
            name: Package name
            cask: If True, get cask info instead of formula

        Returns:
            Dictionary with package info or None if not found
        """
        args = ["info", "--json=v1"]
        if cask:
            args.append("--cask")
        args.append(name)

        try:
            _, stdout, _ = await self._run_command(args, check=False)
            import json

            data = json.loads(stdout)
            if data:
                return data[0]
            return None
        except (InstallationError, json.JSONDecodeError, IndexError):
            return None

    async def update(self) -> tuple[bool, str]:
        """
        Update Homebrew itself.

        Returns:
            Tuple of (success, message)
        """
        try:
            _, stdout, stderr = await self._run_command(["update"], check=True, timeout=300.0)
            return True, "Homebrew updated"
        except InstallationError as e:
            return False, str(e)
        except asyncio.TimeoutError:
            return False, "Brew update timed out"

    async def upgrade(self, name: str | None = None) -> tuple[bool, str]:
        """
        Upgrade packages.

        Args:
            name: Optional package name to upgrade (upgrades all if None)

        Returns:
            Tuple of (success, message)
        """
        args = ["upgrade"]
        if name:
            args.append(name)

        try:
            _, stdout, stderr = await self._run_command(args, check=True, timeout=600.0)
            return True, f"Upgraded {name}" if name else "Upgraded all packages"
        except InstallationError as e:
            return False, str(e)
        except asyncio.TimeoutError:
            return False, "Brew upgrade timed out"
