"""Unit tests for pysetitup.config.validator module."""

import pytest

from pysetitup.config.validator import validate_preset, validate_presets_yaml
from pysetitup.utils.errors import ConfigurationError


class TestValidatePresetsYAML:
    """Test YAML validation with Pydantic."""

    def test_valid_presets_yaml(self) -> None:
        """Test validation succeeds for valid YAML."""
        yaml_content = """
presets:
  minimal:
    name: minimal
    description: Minimal setup
    packages:
      - git
      - fzf
    casks:
      - warp
    npm: []
    taps: []
    vscode: []
"""
        result = validate_presets_yaml(yaml_content)

        assert "minimal" in result.presets
        assert result.presets["minimal"].name == "minimal"
        assert "git" in result.presets["minimal"].packages
        assert "warp" in result.presets["minimal"].casks

    def test_multiple_presets(self) -> None:
        """Test validation with multiple presets."""
        yaml_content = """
presets:
  minimal:
    name: minimal
    description: Minimal
    packages: []
    casks: []
    npm: []
    taps: []
    vscode: []
  developer:
    name: developer
    description: Developer setup
    packages:
      - node
      - go
    casks: []
    npm:
      - typescript
    taps: []
    vscode:
      - ms-python.python
"""
        result = validate_presets_yaml(yaml_content)

        assert len(result.presets) == 2
        assert "minimal" in result.presets
        assert "developer" in result.presets
        assert "node" in result.presets["developer"].packages
        assert "typescript" in result.presets["developer"].npm
        assert "ms-python.python" in result.presets["developer"].vscode

    def test_invalid_yaml_syntax(self) -> None:
        """Test validation fails for invalid YAML syntax."""
        yaml_content = """
presets:
  minimal:
    name: minimal
    description: "Unclosed quote
"""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_presets_yaml(yaml_content)

        assert "Invalid YAML syntax" in str(exc_info.value)

    def test_empty_yaml(self) -> None:
        """Test validation fails for empty YAML."""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_presets_yaml("")

        assert "Empty YAML file" in str(exc_info.value)

    def test_missing_presets_key(self) -> None:
        """Test validation fails when presets key is missing."""
        yaml_content = """
other_key:
  value: test
"""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_presets_yaml(yaml_content)

        assert "validation errors" in str(exc_info.value).lower()

    def test_missing_required_fields(self) -> None:
        """Test validation fails when required fields are missing."""
        yaml_content = """
presets:
  minimal:
    description: Missing name field
    packages: []
"""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_presets_yaml(yaml_content)

        assert "validation errors" in str(exc_info.value).lower()

    def test_invalid_field_type(self) -> None:
        """Test validation fails for invalid field types."""
        yaml_content = """
presets:
  minimal:
    name: minimal
    description: Test
    packages: "should be a list"
    casks: []
    npm: []
    taps: []
    vscode: []
"""
        with pytest.raises(ConfigurationError) as exc_info:
            validate_presets_yaml(yaml_content)

        assert "validation errors" in str(exc_info.value).lower()

    def test_optional_fields_with_defaults(self) -> None:
        """Test that optional fields default to empty lists."""
        yaml_content = """
presets:
  minimal:
    name: minimal
    description: Test
"""
        result = validate_presets_yaml(yaml_content)

        preset = result.presets["minimal"]
        assert preset.packages == []
        assert preset.casks == []
        assert preset.npm == []
        assert preset.taps == []
        assert preset.vscode == []


class TestValidatePreset:
    """Test single preset validation."""

    def test_valid_preset(self) -> None:
        """Test validation succeeds for valid preset dict."""
        preset_data = {
            "name": "minimal",
            "description": "Minimal setup",
            "packages": ["git", "fzf"],
            "casks": ["warp"],
            "npm": [],
            "taps": [],
            "vscode": []
        }

        result = validate_preset(preset_data)

        assert result.name == "minimal"
        assert "git" in result.packages
        assert "warp" in result.casks

    def test_invalid_preset_missing_name(self) -> None:
        """Test validation fails when name is missing."""
        preset_data = {
            "description": "Missing name",
            "packages": []
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_preset(preset_data)

        assert "validation errors" in str(exc_info.value).lower()

    def test_preset_with_all_package_types(self) -> None:
        """Test preset with all package types."""
        preset_data = {
            "name": "full",
            "description": "Full setup",
            "packages": ["git", "node"],
            "casks": ["visual-studio-code"],
            "npm": ["typescript"],
            "taps": ["homebrew/cask-fonts"],
            "vscode": ["ms-python.python"]
        }

        result = validate_preset(preset_data)

        assert len(result.packages) == 2
        assert len(result.casks) == 1
        assert len(result.npm) == 1
        assert len(result.taps) == 1
        assert len(result.vscode) == 1
