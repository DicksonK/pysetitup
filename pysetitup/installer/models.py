"""Shared installation result models using Pydantic for validation."""


from pydantic import BaseModel, Field, field_validator


class BrewInstallResult(BaseModel):
    """
    Result of a Homebrew package installation.

    Attributes
    ----------
    package : str
        Package name that was installed
    success : bool
        Whether installation succeeded
    message : str
        Installation message or error details
    already_installed : bool
        Whether package was already installed
    version : str | None
        Installed version (if available)
    attempts : int
        Number of installation attempts made
    """

    package: str = Field(..., min_length=1, description="Package name")
    success: bool = Field(..., description="Installation success status")
    message: str = Field(default="", description="Installation message")
    already_installed: bool = Field(default=False, description="Already installed flag")
    version: str | None = Field(default=None, description="Package version")
    attempts: int = Field(default=1, ge=0, description="Installation attempts")

    @field_validator("package")
    @classmethod
    def validate_package_name(cls, v: str) -> str:
        """Validate package name is not empty."""
        if not v or not v.strip():
            raise ValueError("Package name cannot be empty")
        return v.strip()


class NpmInstallResult(BaseModel):
    """
    Result of an npm package installation.

    Attributes
    ----------
    package : str
        Package name that was installed
    success : bool
        Whether installation succeeded
    message : str
        Installation message or error details
    already_installed : bool
        Whether package was already installed
    version : str | None
        Installed version (if available)
    batch : bool
        Whether installed as part of batch operation
    """

    package: str = Field(..., min_length=1, description="Package name")
    success: bool = Field(..., description="Installation success status")
    message: str = Field(default="", description="Installation message")
    already_installed: bool = Field(default=False, description="Already installed flag")
    version: str | None = Field(default=None, description="Package version")
    batch: bool = Field(default=False, description="Batch installation flag")

    @field_validator("package")
    @classmethod
    def validate_package_name(cls, v: str) -> str:
        """Validate package name is not empty."""
        if not v or not v.strip():
            raise ValueError("Package name cannot be empty")
        return v.strip()


class VSCodeInstallResult(BaseModel):
    """
    Result of a VS Code extension installation.

    Attributes
    ----------
    extension_id : str
        Extension ID (e.g., 'ms-python.python')
    success : bool
        Whether installation succeeded
    already_installed : bool
        Whether extension was already installed
    error : str | None
        Error message if installation failed
    version : str | None
        Installed version (if available)
    package : str
        Alias for extension_id (for consistency with other installers)
    """

    extension_id: str = Field(..., min_length=1, description="VS Code extension ID")
    success: bool = Field(..., description="Installation success status")
    already_installed: bool = Field(default=False, description="Already installed flag")
    error: str | None = Field(default=None, description="Error message")
    version: str | None = Field(default=None, description="Extension version")

    @field_validator("extension_id")
    @classmethod
    def validate_extension_id(cls, v: str) -> str:
        """Validate extension ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Extension ID cannot be empty")
        return v.strip()

    @property
    def package(self) -> str:
        """Get extension_id as package for consistency with other result types."""
        return self.extension_id
