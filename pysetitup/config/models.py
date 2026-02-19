"""Configuration data models for PySetItUp."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Package(BaseModel):
    """A package available for installation."""

    name: str = Field(..., description="Package name")
    category: str = Field(..., description="Category (e.g., 'CLI Tools', 'Development')")
    type: Literal["formula", "cask", "npm", "vscode"] = Field(..., description="Package type")
    description: Optional[str] = Field(None, description="Package description")
    tap: Optional[str] = Field(None, description="Homebrew tap if needed")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "git",
                "category": "CLI Tools",
                "type": "formula",
                "description": "Distributed version control system",
            }
        }
    }


class Preset(BaseModel):
    """A preset configuration with predefined packages."""

    name: str = Field(..., description="Preset name (minimal, developer, full)")
    description: str = Field(..., description="Preset description")
    packages: list[str] = Field(default_factory=list, description="List of Homebrew formulae")
    casks: list[str] = Field(default_factory=list, description="List of Homebrew casks")
    npm: list[str] = Field(default_factory=list, description="List of npm packages")
    taps: list[str] = Field(default_factory=list, description="List of Homebrew taps")
    vscode: list[str] = Field(default_factory=list, description="List of VS Code extensions")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "minimal",
                "description": "Essential CLI tools",
                "packages": ["git", "fzf", "ripgrep"],
                "casks": ["warp", "rectangle"],
                "npm": [],
                "taps": [],
                "vscode": [],
            }
        }
    }


class DotfilesConfig(BaseModel):
    """Dotfiles repository configuration."""

    repo: str = Field(..., description="Git repository URL")
    branch: Optional[str] = Field(None, description="Branch to checkout")
    stow_dirs: list[str] = Field(
        default_factory=list, description="Directories to stow (link)"
    )


class Config(BaseModel):
    """Main configuration containing all presets and packages."""

    presets: dict[str, Preset] = Field(
        default_factory=dict, description="Available presets"
    )
    packages: list[Package] = Field(
        default_factory=list, description="All available packages"
    )

    def get_preset(self, name: str) -> Optional[Preset]:
        """
        Get a preset by name.

        Args:
            name: Preset name

        Returns:
            Preset or None if not found
        """
        return self.presets.get(name)

    def get_package(self, name: str) -> Optional[Package]:
        """
        Get a package by name.

        Args:
            name: Package name

        Returns:
            Package or None if not found
        """
        for package in self.packages:
            if package.name == name:
                return package
        return None

    def get_packages_by_category(self, category: str) -> list[Package]:
        """
        Get all packages in a category.

        Args:
            category: Category name

        Returns:
            List of packages in the category
        """
        return [pkg for pkg in self.packages if pkg.category == category]

    def get_packages_by_type(self, package_type: str) -> list[Package]:
        """
        Get all packages of a specific type.

        Args:
            package_type: Package type (formula, cask, npm)

        Returns:
            List of packages of the given type
        """
        return [pkg for pkg in self.packages if pkg.type == package_type]

    def get_all_categories(self) -> list[str]:
        """
        Get all unique categories.

        Returns:
            Sorted list of unique category names
        """
        categories = {pkg.category for pkg in self.packages}
        return sorted(categories)
