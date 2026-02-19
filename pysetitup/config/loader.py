"""Configuration loading and management."""

import importlib.resources
from pathlib import Path
from typing import Optional

import yaml

from pysetitup.config.models import Config, Package, Preset
from pysetitup.config.validator import validate_presets_yaml
from pysetitup.utils.errors import ConfigurationError


def load_embedded_presets() -> dict[str, Preset]:
    """
    Load presets from embedded presets.yaml file with Pydantic validation.

    Returns:
        Dictionary mapping preset names to Preset objects

    Raises:
        ConfigurationError: If presets.yaml cannot be loaded or parsed
    """
    try:
        # Load presets.yaml from package data
        presets_yaml = importlib.resources.files("pysetitup.config").joinpath("presets.yaml")
        content = presets_yaml.read_text()

        # Validate using Pydantic
        validated = validate_presets_yaml(content)
        return validated.presets

    except FileNotFoundError as e:
        raise ConfigurationError(f"presets.yaml not found in package: {e}")
    except Exception as e:
        # Re-raise ConfigurationError as-is, wrap others
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(f"Failed to load presets: {e}")


def load_embedded_packages() -> list[Package]:
    """
    Load packages from embedded packages.yaml file.

    The packages.yaml has a structure with categories containing packages.
    This function flattens it into a list of Package objects.

    Returns:
        List of Package objects

    Raises:
        ConfigurationError: If packages.yaml cannot be loaded or parsed
    """
    try:
        # Load packages.yaml from package data
        packages_yaml = importlib.resources.files("pysetitup.config").joinpath("packages.yaml")
        content = packages_yaml.read_text()
        data = yaml.safe_load(content)

        if not data or "categories" not in data:
            raise ConfigurationError(
                "Invalid packages.yaml format: missing 'categories' key"
            )

        # Parse into Pydantic models - flatten categories structure
        packages = []
        for category in data["categories"]:
            category_name = category.get("name", "Unknown")

            for pkg in category.get("packages", []):
                # Determine package type (formula, cask, npm, or vscode)
                # Support both "type: X" and "cask: true"/"npm: true"/"vscode: true" formats
                if "type" in pkg:
                    pkg_type = pkg["type"]
                elif pkg.get("cask", False):
                    pkg_type = "cask"
                elif pkg.get("npm", False):
                    pkg_type = "npm"
                elif pkg.get("vscode", False):
                    pkg_type = "vscode"
                else:
                    pkg_type = "formula"

                packages.append(
                    Package(
                        name=pkg["name"],
                        category=category_name,
                        type=pkg_type,  # type: ignore
                        description=pkg.get("desc"),
                        tap=pkg.get("tap"),
                    )
                )

        return packages
    except FileNotFoundError as e:
        raise ConfigurationError(f"packages.yaml not found in package: {e}")
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Failed to parse packages.yaml: {e}")
    except KeyError as e:
        raise ConfigurationError(f"Invalid package structure: missing {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load packages: {e}")


def load_external_presets(file_path: Path) -> dict[str, Preset]:
    """
    Load presets from an external YAML file with Pydantic validation.

    Args:
        file_path: Path to external presets YAML file

    Returns:
        Dictionary mapping preset names to Preset objects

    Raises:
        ConfigurationError: If file cannot be loaded, parsed, or validated
    """
    if not file_path.exists():
        raise ConfigurationError(f"Presets file not found: {file_path}")

    if not file_path.is_file():
        raise ConfigurationError(f"Not a file: {file_path}")

    try:
        content = file_path.read_text()
        validated = validate_presets_yaml(content)
        return validated.presets
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        raise ConfigurationError(f"Failed to load external presets from {file_path}: {e}")


def load_config(external_presets_file: Optional[Path] = None) -> Config:
    """
    Load the complete configuration (presets + packages).

    Args:
        external_presets_file: Optional path to external presets YAML file.
                               If provided, presets from this file will be merged
                               with embedded presets (external presets take precedence).

    Returns:
        Config object with all presets and packages

    Raises:
        ConfigurationError: If configuration cannot be loaded
    """
    # Load embedded presets
    presets = load_embedded_presets()

    # Load and merge external presets if provided
    if external_presets_file:
        external_presets = load_external_presets(external_presets_file)
        # External presets override embedded ones with same name
        presets.update(external_presets)

    packages = load_embedded_packages()

    return Config(presets=presets, packages=packages)
