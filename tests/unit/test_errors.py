"""Unit tests for pysetitup.utils.errors module."""

import pytest

from pysetitup.utils.errors import (
    AuthenticationError,
    ConfigurationError,
    DependencyError,
    InstallationError,
    NetworkError,
    PySetItUpError,
    SnapshotError,
    StateError,
    SystemError,
)


class TestPySetItUpError:
    """Test the base PySetItUpError exception."""

    def test_base_exception(self) -> None:
        """Test that PySetItUpError can be raised."""
        with pytest.raises(PySetItUpError) as exc_info:
            raise PySetItUpError("Test error")
        assert str(exc_info.value) == "Test error"

    def test_inheritance(self) -> None:
        """Test that PySetItUpError inherits from Exception."""
        assert issubclass(PySetItUpError, Exception)


class TestInstallationError:
    """Test the InstallationError exception."""

    def test_installation_error_with_package(self) -> None:
        """Test InstallationError with package name and message."""
        error = InstallationError("git", "Network timeout")
        assert error.package == "git"
        assert error.message == "Network timeout"
        assert "Failed to install git" in str(error)
        assert "Network timeout" in str(error)

    def test_inheritance(self) -> None:
        """Test that InstallationError inherits from PySetItUpError."""
        assert issubclass(InstallationError, PySetItUpError)


class TestDependencyError:
    """Test the DependencyError exception."""

    def test_dependency_error_without_message(self) -> None:
        """Test DependencyError with only dependency name."""
        error = DependencyError("homebrew")
        assert error.dependency == "homebrew"
        assert "Missing required dependency: homebrew" in str(error)

    def test_dependency_error_with_message(self) -> None:
        """Test DependencyError with dependency name and message."""
        error = DependencyError("git", "Please install via Xcode Command Line Tools")
        assert error.dependency == "git"
        assert "Missing required dependency: git" in str(error)
        assert "Please install via Xcode Command Line Tools" in str(error)

    def test_inheritance(self) -> None:
        """Test that DependencyError inherits from PySetItUpError."""
        assert issubclass(DependencyError, PySetItUpError)


class TestOtherErrors:
    """Test other error types."""

    def test_network_error(self) -> None:
        """Test NetworkError."""
        with pytest.raises(NetworkError) as exc_info:
            raise NetworkError("Connection timeout")
        assert str(exc_info.value) == "Connection timeout"
        assert issubclass(NetworkError, PySetItUpError)

    def test_configuration_error(self) -> None:
        """Test ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Invalid YAML")
        assert str(exc_info.value) == "Invalid YAML"
        assert issubclass(ConfigurationError, PySetItUpError)

    def test_state_error(self) -> None:
        """Test StateError."""
        with pytest.raises(StateError) as exc_info:
            raise StateError("Failed to save state")
        assert str(exc_info.value) == "Failed to save state"
        assert issubclass(StateError, PySetItUpError)

    def test_authentication_error(self) -> None:
        """Test AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Invalid token")
        assert str(exc_info.value) == "Invalid token"
        assert issubclass(AuthenticationError, PySetItUpError)

    def test_snapshot_error(self) -> None:
        """Test SnapshotError."""
        with pytest.raises(SnapshotError) as exc_info:
            raise SnapshotError("Failed to capture snapshot")
        assert str(exc_info.value) == "Failed to capture snapshot"
        assert issubclass(SnapshotError, PySetItUpError)

    def test_system_error(self) -> None:
        """Test SystemError."""
        with pytest.raises(SystemError) as exc_info:
            raise SystemError("Not running on macOS")
        assert str(exc_info.value) == "Not running on macOS"
        assert issubclass(SystemError, PySetItUpError)


class TestErrorHierarchy:
    """Test the error hierarchy."""

    def test_all_errors_inherit_from_pysetitup_error(self) -> None:
        """Test that all custom errors inherit from PySetItUpError."""
        error_classes = [
            InstallationError,
            NetworkError,
            ConfigurationError,
            DependencyError,
            StateError,
            AuthenticationError,
            SnapshotError,
            SystemError,
        ]
        for error_class in error_classes:
            assert issubclass(error_class, PySetItUpError)

    def test_can_catch_all_with_base_exception(self) -> None:
        """Test that PySetItUpError can catch all custom errors."""
        with pytest.raises(PySetItUpError):
            raise InstallationError("pkg", "msg")

        with pytest.raises(PySetItUpError):
            raise DependencyError("dep")

        with pytest.raises(PySetItUpError):
            raise NetworkError("network")
