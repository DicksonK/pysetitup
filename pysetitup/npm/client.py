"""npm command execution client."""

import asyncio
import shutil

from pysetitup.utils.errors import DependencyError, InstallationError


class NpmClient:
    """Client for executing npm commands."""

    def __init__(self, npm_path: str | None = None):
        """
        Initialize NpmClient.

        Args:
            npm_path: Optional path to npm executable (auto-detected if None)

        Raises:
            DependencyError: If npm is not installed
        """
        self.npm_path = npm_path or self._find_npm()
        if not self.npm_path:
            raise DependencyError(
                dependency="npm",
                message="npm is not installed. Install Node.js from https://nodejs.org or via Homebrew: brew install node",
            )

    def _find_npm(self) -> str | None:
        """
        Find the npm executable in PATH.

        Returns:
            Path to npm executable or None if not found
        """
        return shutil.which("npm")

    async def _run_command(
        self,
        args: list[str],
        check: bool = True,
        timeout: float | None = None,
    ) -> tuple[int, str, str]:
        """
        Run an npm command asynchronously.

        Args:
            args: Command arguments (npm is prepended automatically)
            check: If True, raise error on non-zero exit code
            timeout: Optional timeout in seconds

        Returns:
            Tuple of (returncode, stdout, stderr)

        Raises:
            InstallationError: If command fails and check=True
            asyncio.TimeoutError: If command times out
        """
        cmd = [self.npm_path] + args

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
                pkg_name = args[-1] if args else "unknown"
                raise InstallationError(
                    package=pkg_name,
                    message=f"npm command failed: {' '.join(args)}\nExit code: {returncode}\nStderr: {stderr}",
                )

            return returncode, stdout, stderr

        except asyncio.TimeoutError:
            # Kill the process if it times out
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
            raise

    async def install_global(self, packages: list[str], timeout: float | None = 300.0) -> tuple[bool, str]:
        """
        Install npm packages globally (batch install).

        Args:
            packages: List of package names
            timeout: Timeout in seconds (default: 300s = 5 minutes)

        Returns:
            Tuple of (success, message)
        """
        if not packages:
            return True, "No packages to install"

        try:
            args = ["install", "--global"] + packages
            _, stdout, stderr = await self._run_command(args, check=True, timeout=timeout)
            return True, f"Installed {len(packages)} package(s)"
        except InstallationError as e:
            return False, str(e)
        except asyncio.TimeoutError:
            return False, f"Installation timed out after {timeout}s"

    async def install_single(self, package: str, timeout: float | None = 300.0) -> tuple[bool, str]:
        """
        Install a single npm package globally.

        Args:
            package: Package name
            timeout: Timeout in seconds (default: 300s = 5 minutes)

        Returns:
            Tuple of (success, message)
        """
        try:
            _, stdout, stderr = await self._run_command(["install", "--global", package], check=True, timeout=timeout)
            return True, f"Installed {package}"
        except InstallationError as e:
            return False, str(e)
        except asyncio.TimeoutError:
            return False, f"Installation of {package} timed out after {timeout}s"

    async def list_global(self, depth: int = 0) -> list[str]:
        """
        List globally installed npm packages.

        Args:
            depth: Depth of dependencies to show (0 = top-level only)

        Returns:
            List of installed package names
        """
        try:
            _, stdout, _ = await self._run_command(["list", "--global", "--depth", str(depth), "--json"], check=True)
            import json

            data = json.loads(stdout)
            dependencies = data.get("dependencies", {})
            return list(dependencies.keys())
        except (InstallationError, json.JSONDecodeError, KeyError):
            return []

    async def list_global_versions(self, depth: int = 0) -> dict[str, str]:
        """
        List globally installed npm packages with versions.

        Args:
            depth: Depth of dependencies to show (0 = top-level only)

        Returns:
            Dictionary mapping package name to version
        """
        try:
            _, stdout, _ = await self._run_command(["list", "--global", "--depth", str(depth), "--json"], check=True)
            import json

            data = json.loads(stdout)
            dependencies = data.get("dependencies", {})
            versions = {}
            for pkg_name, pkg_info in dependencies.items():
                version = pkg_info.get("version")
                if version:
                    versions[pkg_name] = version
            return versions
        except (InstallationError, json.JSONDecodeError, KeyError):
            return {}

    async def uninstall_global(self, package: str) -> tuple[bool, str]:
        """
        Uninstall a global npm package.

        Args:
            package: Package name

        Returns:
            Tuple of (success, message)
        """
        try:
            _, stdout, stderr = await self._run_command(["uninstall", "--global", package], check=True)
            return True, f"Uninstalled {package}"
        except InstallationError as e:
            return False, str(e)

    async def outdated_global(self) -> list[dict[str, str]]:
        """
        Get list of outdated global packages.

        Returns:
            List of dictionaries with package info
        """
        try:
            _, stdout, _ = await self._run_command(
                ["outdated", "--global", "--json"],
                check=False,  # outdated returns non-zero if packages found
            )
            import json

            data = json.loads(stdout)
            packages = []

            for name, info in data.items():
                packages.append(
                    {
                        "name": name,
                        "current": info.get("current", ""),
                        "wanted": info.get("wanted", ""),
                        "latest": info.get("latest", ""),
                    }
                )

            return packages
        except (json.JSONDecodeError, AttributeError):
            return []

    async def update_global(self, package: str | None = None) -> tuple[bool, str]:
        """
        Update global npm package(s).

        Args:
            package: Optional package name to update (updates all if None)

        Returns:
            Tuple of (success, message)
        """
        args = ["update", "--global"]
        if package:
            args.append(package)

        try:
            _, stdout, stderr = await self._run_command(args, check=True, timeout=300.0)
            return True, f"Updated {package}" if package else "Updated all packages"
        except InstallationError as e:
            return False, str(e)
        except asyncio.TimeoutError:
            return False, "npm update timed out"
