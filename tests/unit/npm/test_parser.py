"""Unit tests for pysetitup.npm.parser module."""


from pysetitup.npm.parser import NpmParser


class TestNpmParser:
    """Test the NpmParser class."""

    def test_parse_list_json(self) -> None:
        """Test parse_list_json extracts package names."""
        json_data = {"dependencies": {"typescript": {}, "eslint": {}, "prettier": {}}}
        packages = NpmParser.parse_list_json(json_data)

        assert set(packages) == {"typescript", "eslint", "prettier"}

    def test_parse_list_json_empty(self) -> None:
        """Test parse_list_json with no dependencies."""
        json_data = {"dependencies": {}}
        packages = NpmParser.parse_list_json(json_data)

        assert packages == []

    def test_parse_outdated_json(self) -> None:
        """Test parse_outdated_json extracts package info."""
        json_data = {
            "typescript": {
                "current": "4.9.0",
                "wanted": "4.9.5",
                "latest": "5.0.0",
            },
            "eslint": {"current": "8.0.0", "wanted": "8.5.0", "latest": "8.5.0"},
        }
        packages = NpmParser.parse_outdated_json(json_data)

        assert len(packages) == 2
        assert packages[0]["name"] == "typescript"
        assert packages[0]["current"] == "4.9.0"
        assert packages[0]["latest"] == "5.0.0"

    def test_is_already_installed_true(self) -> None:
        """Test is_already_installed detects already installed."""
        stderr = "npm WARN already installed typescript@5.0.0"
        assert NpmParser.is_already_installed(stderr) is True

        stderr = "up to date, audited 1 package"
        assert NpmParser.is_already_installed(stderr) is True

        stderr = "skipping action, package already installed"
        assert NpmParser.is_already_installed(stderr) is True

    def test_is_already_installed_false(self) -> None:
        """Test is_already_installed returns False for other errors."""
        stderr = "npm ERR! code E404"
        assert NpmParser.is_already_installed(stderr) is False

        stderr = ""
        assert NpmParser.is_already_installed(stderr) is False

    def test_extract_installed_packages(self) -> None:
        """Test extract_installed_packages finds package names."""
        output = "added typescript@5.0.0\nadded eslint@8.0.0"
        packages = NpmParser.extract_installed_packages(output)

        assert "typescript" in packages
        assert "eslint" in packages

    def test_extract_installed_packages_with_plus(self) -> None:
        """Test extract_installed_packages handles + prefix."""
        output = "+ typescript@5.0.0\n+ eslint@8.0.0"
        packages = NpmParser.extract_installed_packages(output)

        assert "typescript" in packages
        assert "eslint" in packages

    def test_extract_installed_packages_no_duplicates(self) -> None:
        """Test extract_installed_packages removes duplicates."""
        output = "added typescript@5.0.0\nadded typescript@5.0.0"
        packages = NpmParser.extract_installed_packages(output)

        assert packages.count("typescript") == 1

    def test_extract_version(self) -> None:
        """Test extract_version finds version for package."""
        output = "added typescript@5.0.2"
        version = NpmParser.extract_version(output, "typescript")

        assert version == "5.0.2"

    def test_extract_version_not_found(self) -> None:
        """Test extract_version returns None when not found."""
        output = "added eslint@8.0.0"
        version = NpmParser.extract_version(output, "typescript")

        assert version is None

    def test_parse_install_output_success(self) -> None:
        """Test parse_install_output with successful install."""
        stdout = "added typescript@5.0.0"
        stderr = ""

        result = NpmParser.parse_install_output(stdout, stderr)

        assert "typescript" in result["packages"]
        assert result["already_installed"] is False
        assert result["output"] == "added typescript@5.0.0"

    def test_parse_install_output_already_installed(self) -> None:
        """Test parse_install_output detects already installed."""
        stdout = ""
        stderr = "npm WARN already installed typescript@5.0.0"

        result = NpmParser.parse_install_output(stdout, stderr)

        assert result["already_installed"] is True

    def test_parse_error_message(self) -> None:
        """Test parse_error_message extracts meaningful error."""
        stderr = "npm ERR! code E404\nnpm ERR! 404 Not Found"
        message = NpmParser.parse_error_message(stderr)

        assert "E404" in message
        assert "404 Not Found" in message

    def test_parse_error_message_skips_separators(self) -> None:
        """Test parse_error_message skips separator lines."""
        stderr = "npm ERR! code E404\nnpm ERR! ---\nnpm ERR! Details"
        message = NpmParser.parse_error_message(stderr)

        assert "---" not in message

    def test_count_packages_in_output(self) -> None:
        """Test count_packages_in_output finds package count."""
        output = "added 5 packages in 10s"
        count = NpmParser.count_packages_in_output(output)

        assert count == 5

    def test_count_packages_in_output_fallback(self) -> None:
        """Test count_packages_in_output falls back to counting names."""
        output = "added typescript@5.0.0\nadded eslint@8.0.0"
        count = NpmParser.count_packages_in_output(output)

        assert count == 2
