"""YAML configuration validation using Pydantic."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError

from pysetitup.config.models import Preset
from pysetitup.utils.errors import ConfigurationError


class PresetsFile(BaseModel):
    """Model for validating presets YAML file structure."""

    presets: dict[str, Preset] = Field(..., description="Dictionary of preset configurations")

    model_config = {
        "json_schema_extra": {
            "example": {
                "presets": {
                    "minimal": {
                        "name": "minimal",
                        "description": "Essential CLI tools",
                        "packages": ["git", "fzf"],
                        "casks": ["warp"],
                        "npm": [],
                        "taps": [],
                        "vscode": [],
                    }
                }
            }
        }
    }


def validate_presets_yaml(yaml_content: str) -> PresetsFile:
    """
    Validate presets YAML content using Pydantic.

    Args:
        yaml_content: YAML content as string

    Returns:
        Validated PresetsFile object

    Raises:
        ConfigurationError: If YAML is invalid or doesn't match schema
    """
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML syntax: {e}") from e

    if not data:
        raise ConfigurationError("Empty YAML file")

    try:
        return PresetsFile(**data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append(f"  - {field}: {message}")

        error_message = "YAML validation errors:\n" + "\n".join(errors)
        raise ConfigurationError(error_message) from e


def validate_preset(preset_data: dict) -> Preset:
    """
    Validate a single preset configuration.

    Args:
        preset_data: Dictionary containing preset data

    Returns:
        Validated Preset object

    Raises:
        ConfigurationError: If preset data is invalid
    """
    try:
        return Preset(**preset_data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append(f"  - {field}: {message}")

        error_message = "Preset validation errors:\n" + "\n".join(errors)
        raise ConfigurationError(error_message) from e


def validate_presets_file(file_path: Path) -> PresetsFile:
    """
    Validate a presets YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Validated PresetsFile object

    Raises:
        ConfigurationError: If file doesn't exist or is invalid
    """
    if not file_path.exists():
        raise ConfigurationError(f"Presets file not found: {file_path}")

    if not file_path.is_file():
        raise ConfigurationError(f"Not a file: {file_path}")

    try:
        content = file_path.read_text()
    except Exception as e:
        raise ConfigurationError(f"Failed to read presets file: {e}") from e

    return validate_presets_yaml(content)
