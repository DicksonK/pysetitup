"""Unit tests for pysetitup.npm.client module."""

from unittest.mock import AsyncMock, patch

import pytest

from pysetitup.npm.client import NpmClient
from pysetitup.utils.errors import DependencyError


class TestNpmClient:
    """Test the NpmClient class."""

    def test_init_finds_npm(self) -> None:
        """Test NpmClient initialization finds npm in PATH."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()
            assert client.npm_path == "/usr/local/bin/npm"

    def test_init_raises_if_npm_not_found(self) -> None:
        """Test NpmClient raises error if npm not installed."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(DependencyError) as exc_info:
                NpmClient()

            assert "npm" in str(exc_info.value).lower()

    def test_init_with_custom_path(self) -> None:
        """Test NpmClient accepts custom npm path."""
        client = NpmClient(npm_path="/custom/path/npm")
        assert client.npm_path == "/custom/path/npm"

    @pytest.mark.asyncio
    async def test_install_global_success(self) -> None:
        """Test install_global successfully installs packages."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"added 2 packages", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_global(["typescript", "eslint"])

            assert success is True
            assert "2" in message

    @pytest.mark.asyncio
    async def test_install_single_success(self) -> None:
        """Test install_single successfully installs a package."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"added typescript@5.0.0", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_single("typescript")

            assert success is True
            assert "typescript" in message.lower()

    @pytest.mark.asyncio
    async def test_install_failure(self) -> None:
        """Test install handles installation failure."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"Package not found")
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.install_single("nonexistent")

            assert success is False
            assert "failed" in message.lower()

    @pytest.mark.asyncio
    async def test_list_global(self) -> None:
        """Test list_global returns installed packages."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        json_output = '{"dependencies": {"typescript": {}, "eslint": {}, "prettier": {}}}'
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (json_output.encode(), b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            packages = await client.list_global()

            assert set(packages) == {"typescript", "eslint", "prettier"}

    @pytest.mark.asyncio
    async def test_list_global_empty(self) -> None:
        """Test list_global returns empty list when none installed."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b'{"dependencies": {}}', b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            packages = await client.list_global()

            assert packages == []

    @pytest.mark.asyncio
    async def test_uninstall_global(self) -> None:
        """Test uninstall_global removes a package."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"removed typescript", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.uninstall_global("typescript")

            assert success is True
            assert "typescript" in message.lower()

    @pytest.mark.asyncio
    async def test_outdated_global(self) -> None:
        """Test outdated_global returns outdated packages."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        json_output = '{"typescript": {"current": "4.9.0", "wanted": "4.9.5", "latest": "5.0.0"}}'
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (json_output.encode(), b"")
        mock_proc.returncode = 1  # npm outdated returns non-zero

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            packages = await client.outdated_global()

            assert len(packages) == 1
            assert packages[0]["name"] == "typescript"
            assert packages[0]["current"] == "4.9.0"
            assert packages[0]["latest"] == "5.0.0"

    @pytest.mark.asyncio
    async def test_update_global_all(self) -> None:
        """Test update_global without package name updates all."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"updated packages", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.update_global()

            assert success is True
            assert "all" in message.lower()

    @pytest.mark.asyncio
    async def test_update_global_specific(self) -> None:
        """Test update_global with package name updates that package."""
        with patch("shutil.which", return_value="/usr/local/bin/npm"):
            client = NpmClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"updated typescript", b"")
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            success, message = await client.update_global("typescript")

            assert success is True
            assert "typescript" in message.lower()
