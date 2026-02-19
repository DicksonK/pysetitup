"""Custom exception hierarchy for PySetItUp."""


class PySetItUpError(Exception):
    """Base exception for all PySetItUp errors."""

    pass


class InstallationError(PySetItUpError):
    """Exception raised when package installation fails."""

    def __init__(self, package: str, message: str) -> None:
        self.package = package
        self.message = message
        super().__init__(f"Failed to install {package}: {message}")


class NetworkError(PySetItUpError):
    """Exception raised when network operations fail."""

    pass


class ConfigurationError(PySetItUpError):
    """Exception raised when configuration is invalid or missing."""

    pass


class DependencyError(PySetItUpError):
    """Exception raised when required dependencies are missing."""

    def __init__(self, dependency: str, message: str = "") -> None:
        self.dependency = dependency
        msg = f"Missing required dependency: {dependency}"
        if message:
            msg += f" - {message}"
        super().__init__(msg)


class StateError(PySetItUpError):
    """Exception raised when state operations fail."""

    pass


class AuthenticationError(PySetItUpError):
    """Exception raised when authentication fails."""

    pass


class SnapshotError(PySetItUpError):
    """Exception raised when snapshot operations fail."""

    pass


class SystemError(PySetItUpError):
    """Exception raised when system operations fail."""

    pass


class CommandError(PySetItUpError):
    """Exception raised when external command execution fails."""

    pass
