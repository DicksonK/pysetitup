"""Homebrew output parser."""

import re


class BrewParser:
    """Parser for Homebrew command output."""

    @staticmethod
    def parse_list(output: str) -> list[str]:
        """
        Parse output from 'brew list' command.

        Args:
            output: Raw output from brew list

        Returns:
            List of package names

        Example:
            >>> output = "git\\nnode\\npython@3.11"
            >>> BrewParser.parse_list(output)
            ['git', 'node', 'python@3.11']
        """
        if not output.strip():
            return []

        packages = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                packages.append(line)

        return packages

    @staticmethod
    def parse_info_json(json_data: dict) -> dict[str, str]:
        """
        Parse JSON output from 'brew info --json=v1'.

        Args:
            json_data: Parsed JSON data from brew info

        Returns:
            Dictionary with package information

        Example:
            >>> data = {"name": "git", "version": "2.40.0", "desc": "Version control"}
            >>> info = BrewParser.parse_info_json(data)
            >>> info["name"]
            'git'
        """
        return {
            "name": json_data.get("name", ""),
            "version": json_data.get("version", ""),
            "description": json_data.get("desc", ""),
            "homepage": json_data.get("homepage", ""),
            "installed": bool(json_data.get("installed", [])),
        }

    @staticmethod
    def parse_tap_output(output: str) -> list[str]:
        """
        Parse output from 'brew tap' command.

        Args:
            output: Raw output from brew tap

        Returns:
            List of tap names

        Example:
            >>> output = "homebrew/core\\nhomebrew/cask\\ncustom/tap"
            >>> BrewParser.parse_tap_output(output)
            ['homebrew/core', 'homebrew/cask', 'custom/tap']
        """
        if not output.strip():
            return []

        taps = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line and "/" in line:  # Taps should have format "owner/repo"
                taps.append(line)

        return taps

    @staticmethod
    def is_already_installed(stderr: str) -> bool:
        """
        Check if package is already installed based on error message.

        Args:
            stderr: Error output from brew install

        Returns:
            True if package is already installed

        Example:
            >>> stderr = "Warning: git 2.40.0 is already installed"
            >>> BrewParser.is_already_installed(stderr)
            True
        """
        patterns = [
            r"is already installed",
            r"already installed",
            r"already up-to-date",
        ]

        for pattern in patterns:
            if re.search(pattern, stderr, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def extract_version(output: str) -> str | None:
        """
        Extract version number from brew output.

        Args:
            output: Output containing version information

        Returns:
            Version string or None if not found

        Example:
            >>> output = "git 2.40.0 is already installed"
            >>> BrewParser.extract_version(output)
            '2.40.0'
        """
        # Match version patterns like "2.40.0", "1.2.3-beta", "3.11.1"
        version_pattern = r"\b(\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)\b"
        match = re.search(version_pattern, output)

        if match:
            return match.group(1)

        return None

    @staticmethod
    def parse_install_output(stdout: str, stderr: str) -> dict[str, any]:
        """
        Parse output from brew install command.

        Args:
            stdout: Standard output from install command
            stderr: Standard error from install command

        Returns:
            Dictionary with installation info

        Example:
            >>> stdout = "Installing git..."
            >>> stderr = "Warning: git 2.40.0 is already installed"
            >>> result = BrewParser.parse_install_output(stdout, stderr)
            >>> result["already_installed"]
            True
        """
        return {
            "already_installed": BrewParser.is_already_installed(stderr),
            "version": BrewParser.extract_version(stdout + stderr),
            "output": stdout.strip(),
            "errors": stderr.strip(),
        }

    @staticmethod
    def parse_outdated(output: str) -> list[dict[str, str]]:
        """
        Parse output from 'brew outdated' command.

        Args:
            output: Raw output from brew outdated

        Returns:
            List of dictionaries with outdated package info

        Example:
            >>> output = "git (2.39.0) < 2.40.0\\nnode (18.0.0) < 19.0.0"
            >>> packages = BrewParser.parse_outdated(output)
            >>> packages[0]["name"]
            'git'
        """
        if not output.strip():
            return []

        packages = []
        # Format: "package_name (current_version) < new_version"
        pattern = r"(\S+)\s+\(([\d.]+(?:-[\w.]+)?)\)\s+<\s+([\d.]+(?:-[\w.]+)?)"

        for line in output.strip().split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                packages.append(
                    {
                        "name": match.group(1),
                        "current_version": match.group(2),
                        "new_version": match.group(3),
                    }
                )

        return packages
