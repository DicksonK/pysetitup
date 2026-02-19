"""VS Code extension client for managing extensions."""

import asyncio
import json
from typing import Optional

from pysetitup.utils.errors import CommandError


class VSCodeClient:
    """Client for VS Code extension management using 'code' CLI."""

    def __init__(self, code_command: str = "code") -> None:
        """
        Initialize VS Code client.

        Args:
            code_command: The command to use for VS Code CLI (default: "code")
        """
        self.code_command = code_command

    async def _run_command(
        self, args: list[str], check: bool = True
    ) -> tuple[int, str, str]:
        """
        Run a VS Code CLI command.

        Args:
            args: Command arguments
            check: Whether to raise on non-zero exit code

        Returns:
            Tuple of (exit_code, stdout, stderr)

        Raises:
            CommandError: If check=True and command fails
        """
        cmd = [self.code_command] + args

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await proc.communicate()
            stdout = stdout_bytes.decode("utf-8")
            stderr = stderr_bytes.decode("utf-8")

            exit_code = proc.returncode or 0

            if check and exit_code != 0:
                raise CommandError(
                    f"VS Code command failed: {' '.join(cmd)}\n{stderr}"
                )

            return exit_code, stdout, stderr
        except FileNotFoundError:
            raise CommandError(
                f"VS Code CLI not found. Make sure '{self.code_command}' is in your PATH. "
                "You may need to install it via VS Code > Command Palette > "
                "'Shell Command: Install 'code' command in PATH'"
            )

    async def list_extensions(self) -> list[str]:
        """
        List installed VS Code extensions.

        Returns:
            List of extension IDs (e.g., ["ms-python.python", "dbaeumer.vscode-eslint"])

        Raises:
            CommandError: If listing fails
        """
        _, stdout, _ = await self._run_command(["--list-extensions"], check=True)

        extensions = [line.strip() for line in stdout.strip().split("\n") if line.strip()]
        return extensions

    async def list_extensions_with_versions(self) -> dict[str, str]:
        """
        List installed VS Code extensions with versions.

        Returns:
            Dictionary mapping extension ID to version
            Example: {"ms-python.python": "2024.0.0"}

        Raises:
            CommandError: If listing fails
        """
        _, stdout, _ = await self._run_command(
            ["--list-extensions", "--show-versions"], check=True
        )

        extensions = {}
        for line in stdout.strip().split("\n"):
            if line.strip() and "@" in line:
                parts = line.strip().split("@")
                if len(parts) == 2:
                    extension_id = parts[0]
                    version = parts[1]
                    extensions[extension_id] = version

        return extensions

    async def install_extension(
        self, extension_id: str, force: bool = False
    ) -> tuple[bool, str]:
        """
        Install a VS Code extension.

        Args:
            extension_id: Extension ID (e.g., "ms-python.python")
            force: Whether to force install even if already installed

        Returns:
            Tuple of (success: bool, message: str)
        """
        args = ["--install-extension", extension_id]
        if force:
            args.append("--force")

        try:
            exit_code, stdout, stderr = await self._run_command(args, check=False)

            if exit_code == 0:
                # Check if already installed
                if "is already installed" in stdout.lower() or "is already installed" in stderr.lower():
                    return True, f"Extension {extension_id} is already installed"
                return True, f"Successfully installed {extension_id}"
            else:
                return False, f"Failed to install {extension_id}: {stderr}"
        except CommandError as e:
            return False, str(e)

    async def uninstall_extension(self, extension_id: str) -> tuple[bool, str]:
        """
        Uninstall a VS Code extension.

        Args:
            extension_id: Extension ID to uninstall

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            exit_code, stdout, stderr = await self._run_command(
                ["--uninstall-extension", extension_id], check=False
            )

            if exit_code == 0:
                return True, f"Successfully uninstalled {extension_id}"
            else:
                return False, f"Failed to uninstall {extension_id}: {stderr}"
        except CommandError as e:
            return False, str(e)

    async def is_installed(self) -> bool:
        """
        Check if VS Code CLI is available.

        Returns:
            True if 'code' command is available, False otherwise
        """
        try:
            exit_code, _, _ = await self._run_command(["--version"], check=False)
            return exit_code == 0
        except CommandError:
            return False

    async def get_version(self) -> Optional[str]:
        """
        Get VS Code version.

        Returns:
            Version string or None if not available
        """
        try:
            _, stdout, _ = await self._run_command(["--version"], check=True)
            lines = stdout.strip().split("\n")
            if lines:
                return lines[0].strip()
            return None
        except CommandError:
            return None
