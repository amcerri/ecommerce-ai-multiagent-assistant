"""
Unit tests for storage infrastructure.

Tests for app.infrastructure.storage.local_storage.LocalStorage.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config.exceptions import StorageException, ValidationException
from app.infrastructure.storage.local_storage import LocalStorage


class TestLocalStorage:
    """Tests for LocalStorage class."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage(self, temp_dir: Path) -> LocalStorage:
        """Create LocalStorage instance with temp directory."""
        with patch("app.infrastructure.storage.local_storage.get_settings") as mock_settings:
            mock_settings.return_value.storage_path = str(temp_dir)
            return LocalStorage()

    @pytest.mark.asyncio
    async def test_save_valid_file(self, storage: LocalStorage) -> None:
        """Test saving valid file."""
        content = b"test content"
        file_path = await storage.save(content, "test.pdf", "commerce")
        assert file_path is not None
        assert "commerce" in file_path
        assert file_path.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_save_invalid_file_type(self, storage: LocalStorage) -> None:
        """Test saving invalid file type."""
        content = b"test content"
        with pytest.raises(ValidationException):
            await storage.save(content, "test.exe", "commerce")

    @pytest.mark.asyncio
    async def test_get_existing_file(self, storage: LocalStorage) -> None:
        """Test getting existing file."""
        content = b"test content"
        file_path = await storage.save(content, "test.pdf", "commerce")
        retrieved = await storage.get(file_path)
        assert retrieved == content

    @pytest.mark.asyncio
    async def test_get_nonexistent_file(self, storage: LocalStorage) -> None:
        """Test getting nonexistent file."""
        with pytest.raises(StorageException):
            await storage.get("nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_delete_file(self, storage: LocalStorage) -> None:
        """Test deleting file."""
        content = b"test content"
        file_path = await storage.save(content, "test.pdf", "commerce")
        await storage.delete(file_path)
        # File should not exist after deletion
        assert await storage.exists(file_path) is False

    @pytest.mark.asyncio
    async def test_exists(self, storage: LocalStorage) -> None:
        """Test checking file existence."""
        content = b"test content"
        file_path = await storage.save(content, "test.pdf", "commerce")
        assert await storage.exists(file_path) is True
        assert await storage.exists("nonexistent/file.pdf") is False

