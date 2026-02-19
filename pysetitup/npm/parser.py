"""npm output parser."""

import re


class NpmParser:
    """Parser for npm command output."""

    @staticmethod
    def parse_list_json(json_data: dict) -> list[str]:
        """
        Parse JSON output from 'npm list --global --json'.

        Args:
            json_data: Parsed JSON data from npm list

        Returns:
            List of package names

        Example:
            >>> data = {"dependencies": {"typescript": {}, "eslint": {}}}
            >>> NpmParser.parse_list_json(data)
            ['typescript', 'eslint']
        """
        dependencies = json_data.get("dependencies", {})
        return list(dependencies.keys())

    @staticmethod
    def parse_outdated_json(json_data: dict) -> list[dict[str, str]]:
        """
        Parse JSON output from 'npm outdated --global --json'.

        Args:
            json_data: Parsed JSON data from npm outdated

        Returns:
            List of dictionaries with package info

        Example:
            >>> data = {"typescript": {"current": "4.9.0", "latest": "5.0.0"}}
            >>> packages = NpmParser.parse_outdated_json(data)
            >>> packages[0]["name"]
            'typescript'
        """
        packages = []
        for name, info in json_data.items():
            packages.append(
                {
                    "name": name,
                    "current": info.get("current", ""),
                    "wanted": info.get("wanted", ""),
                    "latest": info.get("latest", ""),
                }
            )
        return packages

    @staticmethod
    def is_already_installed(stderr: str) -> bool:
        """
        Check if package is already installed based on error message.

        Args:
            stderr: Error output from npm install

        Returns:
            True if package is already installed or up-to-date

        Example:
            >>> stderr = "npm WARN already installed typescript@5.0.0"
            >>> NpmParser.is_already_installed(stderr)
            True
        """
        patterns = [
            r"already installed",
            r"up to date",
            r"skipping action",
        ]

        for pattern in patterns:
            if re.search(pattern, stderr, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def extract_installed_packages(stdout: str) -> list[str]:
        """
        Extract package names from npm install output.

        Args:
            stdout: Standard output from npm install

        Returns:
            List of installed package names

        Example:
            >>> output = "added typescript@5.0.0\\nadded eslint@8.0.0"
            >>> NpmParser.extract_installed_packages(output)
            ['typescript', 'eslint']
        """
        packages = []
        # Match patterns like "added package-name@version" or "+ package-name@version"
        patterns = [
            r"(?:added|installed|\+)\s+([a-z0-9@/\-_]+)@",
            r"(?:added|installed|\+)\s+([a-z0-9@/\-_]+)\s",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, stdout, re.IGNORECASE | re.MULTILINE)
            packages.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_packages = []
        for pkg in packages:
            if pkg not in seen:
                seen.add(pkg)
                unique_packages.append(pkg)

        return unique_packages

    @staticmethod
    def extract_version(output: str, package: str) -> str | None:
        """
        Extract version number for a specific package from npm output.

        Args:
            output: Output containing version information
            package: Package name to find version for

        Returns:
            Version string or None if not found

        Example:
            >>> output = "added typescript@5.0.2"
            >>> NpmParser.extract_version(output, "typescript")
            '5.0.2'
        """
        # Match pattern: package@version
        pattern = rf"{re.escape(package)}@([\d.]+(?:-[\w.]+)?)"
        match = re.search(pattern, output)

        if match:
            return match.group(1)

        return None

    @staticmethod
    def parse_install_output(stdout: str, stderr: str) -> dict[str, any]:
        """
        Parse output from npm install command.

        Args:
            stdout: Standard output from install command
            stderr: Standard error from install command

        Returns:
            Dictionary with installation info

        Example:
            >>> stdout = "added typescript@5.0.0"
            >>> stderr = ""
            >>> result = NpmParser.parse_install_output(stdout, stderr)
            >>> result["packages"]
            ['typescript']
        """
        return {
            "packages": NpmParser.extract_installed_packages(stdout),
            "already_installed": NpmParser.is_already_installed(stderr),
            "output": stdout.strip(),
            "errors": stderr.strip(),
        }

    @staticmethod
    def parse_error_message(stderr: str) -> str:
        """
        Extract meaningful error message from npm stderr.

        Args:
            stderr: Error output from npm

        Returns:
            Cleaned error message

        Example:
            >>> stderr = "npm ERR! code E404\\nnpm ERR! 404 Not Found"
            >>> NpmParser.parse_error_message(stderr)
            'code E404: 404 Not Found'
        """
        lines = stderr.strip().split("\n")
        error_lines = []

        for line in lines:
            # Skip npm ERR! prefix
            if line.startswith("npm ERR!"):
                cleaned = line.replace("npm ERR!", "").strip()
                if cleaned and not cleaned.startswith("---"):  # Skip separator lines
                    error_lines.append(cleaned)

        if error_lines:
            return ": ".join(error_lines[:2])  # Return first 2 error lines
        return stderr.strip()

    @staticmethod
    def count_packages_in_output(stdout: str) -> int:
        """
        Count number of packages mentioned in npm install output.

        Args:
            stdout: Standard output from npm install

        Returns:
            Number of packages

        Example:
            >>> output = "added 3 packages in 5s"
            >>> NpmParser.count_packages_in_output(output)
            3
        """
        # Match patterns like "added X packages" or "updated X packages"
        pattern = r"(?:added|installed|updated)\s+(\d+)\s+packages?"
        match = re.search(pattern, stdout, re.IGNORECASE)

        if match:
            return int(match.group(1))

        # Fallback: count individual package installations
        return len(NpmParser.extract_installed_packages(stdout))
