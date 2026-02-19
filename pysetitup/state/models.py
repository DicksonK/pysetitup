"""State data models for PySetItUp."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PackageType(str, Enum):
    """Package type enumeration."""

    FORMULA = "formula"
    CASK = "cask"
    NPM = "npm"
    VSCODE = "vscode"


class InstallState(BaseModel):
    """State of installed packages and configuration."""

    version: str = Field(default="2.0.0", description="State file format version")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last time state was updated")
    installed_formulae: list[str] = Field(default_factory=list, description="List of installed Homebrew formulae")
    installed_casks: list[str] = Field(default_factory=list, description="List of installed Homebrew casks")
    installed_npm: list[str] = Field(default_factory=list, description="List of installed npm packages")
    installed_vscode: list[str] = Field(default_factory=list, description="List of installed VSCode extensions")
    selected_preset: str | None = Field(default=None, description="Selected preset name")
    completed_steps: list[str] = Field(default_factory=list, description="List of completed installation steps")
    git_configured: bool = Field(default=False, description="Whether Git has been configured")
    shell_configured: bool = Field(default=False, description="Whether shell has been configured")
    dotfiles_configured: bool = Field(default=False, description="Whether dotfiles have been linked")
    macos_configured: bool = Field(default=False, description="Whether macOS preferences have been set")

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "json_schema_extra": {
            "example": {
                "version": "2.0.0",
                "last_updated": "2024-02-14T10:30:00Z",
                "installed_formulae": ["git", "fzf", "ripgrep"],
                "installed_casks": ["docker", "vscode"],
                "installed_npm": ["typescript", "eslint"],
                "selected_preset": "developer",
                "completed_steps": ["git_config", "packages", "npm", "shell"],
                "git_configured": True,
                "shell_configured": True,
                "dotfiles_configured": False,
                "macos_configured": False,
            }
        },
    }
