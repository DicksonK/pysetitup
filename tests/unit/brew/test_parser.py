"""Unit tests for pysetitup.brew.parser module."""


from pysetitup.brew.parser import BrewParser


class TestBrewParser:
    """Test the BrewParser class."""

    def test_parse_list_with_packages(self) -> None:
        """Test parse_list extracts package names."""
        output = "git\nnode\npython@3.11\nfzf"
        packages = BrewParser.parse_list(output)

        assert packages == ["git", "node", "python@3.11", "fzf"]

    def test_parse_list_empty(self) -> None:
        """Test parse_list with empty output."""
        assert BrewParser.parse_list("") == []
        assert BrewParser.parse_list("\n\n") == []

    def test_parse_list_ignores_comments(self) -> None:
        """Test parse_list ignores comment lines."""
        output = "git\n# comment\nnode\n# another comment\npython"
        packages = BrewParser.parse_list(output)

        assert packages == ["git", "node", "python"]

    def test_parse_list_strips_whitespace(self) -> None:
        """Test parse_list strips whitespace."""
        output = "  git  \n  node  \n  python  "
        packages = BrewParser.parse_list(output)

        assert packages == ["git", "node", "python"]

    def test_parse_info_json(self) -> None:
        """Test parse_info_json extracts package info."""
        json_data = {
            "name": "git",
            "version": "2.40.0",
            "desc": "Distributed version control system",
            "homepage": "https://git-scm.com",
            "installed": [{"version": "2.40.0"}],
        }

        info = BrewParser.parse_info_json(json_data)

        assert info["name"] == "git"
        assert info["version"] == "2.40.0"
        assert info["description"] == "Distributed version control system"
        assert info["homepage"] == "https://git-scm.com"
        assert info["installed"] is True

    def test_parse_info_json_not_installed(self) -> None:
        """Test parse_info_json with package not installed."""
        json_data = {
            "name": "git",
            "version": "2.40.0",
            "desc": "Version control",
            "installed": [],
        }

        info = BrewParser.parse_info_json(json_data)

        assert info["installed"] is False

    def test_parse_tap_output(self) -> None:
        """Test parse_tap_output extracts tap names."""
        output = "homebrew/core\nhomebrew/cask\ncustom/tap"
        taps = BrewParser.parse_tap_output(output)

        assert taps == ["homebrew/core", "homebrew/cask", "custom/tap"]

    def test_parse_tap_output_empty(self) -> None:
        """Test parse_tap_output with empty output."""
        assert BrewParser.parse_tap_output("") == []

    def test_parse_tap_output_filters_invalid(self) -> None:
        """Test parse_tap_output filters lines without /."""
        output = "homebrew/core\ninvalid\nhomebrew/cask"
        taps = BrewParser.parse_tap_output(output)

        assert taps == ["homebrew/core", "homebrew/cask"]

    def test_is_already_installed_true(self) -> None:
        """Test is_already_installed detects already installed."""
        stderr = "Warning: git 2.40.0 is already installed and up-to-date"
        assert BrewParser.is_already_installed(stderr) is True

        stderr = "git is already installed"
        assert BrewParser.is_already_installed(stderr) is True

        stderr = "already up-to-date"
        assert BrewParser.is_already_installed(stderr) is True

    def test_is_already_installed_false(self) -> None:
        """Test is_already_installed returns False for other errors."""
        stderr = "Error: Package not found"
        assert BrewParser.is_already_installed(stderr) is False

        stderr = ""
        assert BrewParser.is_already_installed(stderr) is False

    def test_is_already_installed_case_insensitive(self) -> None:
        """Test is_already_installed is case insensitive."""
        stderr = "WARNING: Git is ALREADY INSTALLED"
        assert BrewParser.is_already_installed(stderr) is True

    def test_extract_version(self) -> None:
        """Test extract_version finds version numbers."""
        output = "git 2.40.0 is already installed"
        assert BrewParser.extract_version(output) == "2.40.0"

        output = "Installing node 19.5.0"
        assert BrewParser.extract_version(output) == "19.5.0"

        output = "python@3.11"
        assert BrewParser.extract_version(output) == "3.11"

    def test_extract_version_with_beta(self) -> None:
        """Test extract_version handles pre-release versions."""
        output = "Installing rust 1.68.0-beta.1"
        assert BrewParser.extract_version(output) == "1.68.0-beta.1"

    def test_extract_version_not_found(self) -> None:
        """Test extract_version returns None when no version."""
        output = "Package not found"
        assert BrewParser.extract_version(output) is None

    def test_parse_install_output_success(self) -> None:
        """Test parse_install_output with successful install."""
        stdout = "Installing git 2.40.0..."
        stderr = ""

        result = BrewParser.parse_install_output(stdout, stderr)

        assert result["already_installed"] is False
        assert result["version"] == "2.40.0"
        assert result["output"] == "Installing git 2.40.0..."
        assert result["errors"] == ""

    def test_parse_install_output_already_installed(self) -> None:
        """Test parse_install_output detects already installed."""
        stdout = ""
        stderr = "Warning: git 2.40.0 is already installed"

        result = BrewParser.parse_install_output(stdout, stderr)

        assert result["already_installed"] is True
        assert result["version"] == "2.40.0"

    def test_parse_install_output_with_errors(self) -> None:
        """Test parse_install_output preserves error messages."""
        stdout = "Downloading..."
        stderr = "Error: checksum mismatch"

        result = BrewParser.parse_install_output(stdout, stderr)

        assert result["errors"] == "Error: checksum mismatch"
        assert result["already_installed"] is False

    def test_parse_outdated(self) -> None:
        """Test parse_outdated extracts package info."""
        output = "git (2.39.0) < 2.40.0\nnode (18.0.0) < 19.0.0"
        packages = BrewParser.parse_outdated(output)

        assert len(packages) == 2
        assert packages[0]["name"] == "git"
        assert packages[0]["current_version"] == "2.39.0"
        assert packages[0]["new_version"] == "2.40.0"
        assert packages[1]["name"] == "node"
        assert packages[1]["current_version"] == "18.0.0"
        assert packages[1]["new_version"] == "19.0.0"

    def test_parse_outdated_empty(self) -> None:
        """Test parse_outdated with no outdated packages."""
        assert BrewParser.parse_outdated("") == []
        assert BrewParser.parse_outdated("\n") == []

    def test_parse_outdated_with_beta(self) -> None:
        """Test parse_outdated handles pre-release versions."""
        output = "rust (1.67.0) < 1.68.0-beta.1"
        packages = BrewParser.parse_outdated(output)

        assert len(packages) == 1
        assert packages[0]["name"] == "rust"
        assert packages[0]["new_version"] == "1.68.0-beta.1"
