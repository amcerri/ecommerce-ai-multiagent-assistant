"""
Local file storage (file storage system for POC).

Overview
  Provides local file storage system for POC (no cloud costs). Organizes files
  by type and date (YYYY/MM/DD structure), generates unique filenames using UUID,
  and validates file types and sizes. Implements security validation to prevent
  path traversal attacks.

Design
  - **Local Storage**: Uses local filesystem (no S3/MinIO for POC).
  - **Organization**: Files organized by type and date (type/YYYY/MM/DD/uuid.ext).
  - **Unique Names**: Uses UUID4 for unique filenames.
  - **Security**: Validates paths to prevent path traversal attacks.
  - **Validation**: Uses app.utils.validation for file type and size validation.

Integration
  - Consumes: app.config.settings, app.utils.validation, app.config.exceptions.
  - Returns: File paths and file contents.
  - Used by: All agents and services that need file storage.
  - Observability: Logs file operations and errors.

Usage
  >>> from app.infrastructure.storage import get_storage
  >>> storage = get_storage()
  >>> file_path = await storage.save(file_content, "document.pdf", "commerce")
  >>> content = await storage.get(file_path)
"""

import asyncio
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.config.exceptions import StorageException, ValidationException
from app.config.settings import get_settings
from app.utils.validation import validate_file


class LocalStorage:
    """Local file storage system.

    Provides file storage operations (save, get, delete, exists) with
    organization by type and date. Files are stored in structure:
    {base_path}/{file_type}/{YYYY}/{MM}/{DD}/{uuid}.{ext}

    Attributes:
        base_path: Base path for file storage (from settings).

    Note:
        Implements security validation to prevent path traversal attacks.
        Creates directories automatically if they don't exist.
    """

    def __init__(self) -> None:
        """Initialize local storage.

        Gets storage path from settings, creates Path object, and
        creates base directory if it doesn't exist.
        """
        settings = get_settings()
        self.base_path = Path(settings.storage_path).resolve()
        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
    ) -> str:
        """Save file to local storage.

        Validates file (type and size), generates unique filename using UUID,
        creates directory structure (type/YYYY/MM/DD), and saves file.
        Returns relative path for database storage.

        Args:
            file_content: File content in bytes.
            filename: Original filename with extension.
            file_type: File type ("commerce", "knowledge", "analytics").

        Returns:
            Relative file path (e.g., "commerce/2024/11/14/uuid.pdf").

        Raises:
            ValidationException: If file type or size is invalid.
            StorageException: If file save operation fails.
        """
        # Validate file (type and size)
        file_size = len(file_content)
        validate_file(filename, file_size)

        # Generate path with unique filename
        file_path = self._generate_path(file_type, filename)

        try:
            # Save file (async write)
            await asyncio.to_thread(file_path.write_bytes, file_content)

            # Return relative path (for database storage)
            relative_path = file_path.relative_to(self.base_path)
            return str(relative_path)
        except Exception as e:
            raise StorageException(
                message=f"Failed to save file: {filename}",
                details={"error": str(e), "file_type": file_type},
            ) from e

    async def get(self, file_path: str) -> bytes:
        """Get file content from storage.

        Reads file from storage using relative path. Validates that path
        is within base_path to prevent path traversal attacks.

        Args:
            file_path: Relative file path (stored in database).

        Returns:
            File content in bytes.

        Raises:
            StorageException: If file not found or path invalid.
        """
        # Validate and normalize path (security)
        validated_path = self._validate_path(file_path)

        try:
            # Read file (async read)
            content = await asyncio.to_thread(validated_path.read_bytes)
            return content
        except FileNotFoundError:
            raise StorageException(
                message=f"File not found: {file_path}",
                details={"file_path": file_path},
            )
        except Exception as e:
            raise StorageException(
                message=f"Failed to read file: {file_path}",
                details={"error": str(e), "file_path": file_path},
            ) from e

    async def delete(self, file_path: str) -> None:
        """Delete file from storage.

        Deletes file from storage using relative path. Validates that path
        is within base_path. Operation is idempotent (doesn't fail if file
        doesn't exist).

        Args:
            file_path: Relative file path.

        Raises:
            StorageException: If path is invalid (outside base_path).
        """
        # Validate and normalize path (security)
        validated_path = self._validate_path(file_path)

        try:
            # Delete file if exists (idempotent)
            if validated_path.exists():
                await asyncio.to_thread(validated_path.unlink)
        except Exception as e:
            raise StorageException(
                message=f"Failed to delete file: {file_path}",
                details={"error": str(e), "file_path": file_path},
            ) from e

    async def exists(self, file_path: str) -> bool:
        """Check if file exists in storage.

        Verifies file existence using relative path. Validates that path
        is within base_path.

        Args:
            file_path: Relative file path.

        Returns:
            True if file exists, False otherwise.

        Raises:
            StorageException: If path is invalid (outside base_path).
        """
        try:
            # Validate and normalize path (security)
            validated_path = self._validate_path(file_path)
            # Check existence (async)
            return await asyncio.to_thread(validated_path.exists)
        except StorageException:
            # Re-raise storage exceptions
            raise
        except Exception:
            # Return False for other errors
            return False

    def _generate_path(self, file_type: str, filename: str) -> Path:
        """Generate complete file path with directory structure.

        Generates path with structure: {base_path}/{file_type}/{YYYY}/{MM}/{DD}/{uuid}.{ext}
        Creates directories if they don't exist.

        Args:
            file_type: File type ("commerce", "knowledge", "analytics").
            filename: Original filename with extension.

        Returns:
            Complete file path (Path object).
        """
        # Get current date components
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day

        # Generate unique filename
        unique_id = uuid4()
        extension = Path(filename).suffix

        # Build path: {base_path}/{file_type}/{YYYY}/{MM}/{DD}/{uuid}.{ext}
        file_path = (
            self.base_path
            / file_type
            / str(year)
            / f"{month:02d}"
            / f"{day:02d}"
            / f"{unique_id}{extension}"
        )

        # Create directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        return file_path

    def _validate_path(self, file_path: str) -> Path:
        """Validate and normalize file path (security).

        Validates that file path is within base_path to prevent path
        traversal attacks. Resolves and normalizes path before validation.

        Args:
            file_path: Relative file path.

        Returns:
            Validated absolute path (Path object).

        Raises:
            StorageException: If path is invalid (outside base_path).
        """
        # Construct absolute path
        absolute_path = (self.base_path / file_path).resolve()

        # Validate that resolved path is within base_path (prevent path traversal)
        try:
            absolute_path.relative_to(self.base_path.resolve())
        except ValueError:
            raise StorageException(
                message=f"Invalid file path (outside base_path): {file_path}",
                details={
                    "file_path": file_path,
                    "base_path": str(self.base_path),
                },
            )

        return absolute_path


@lru_cache()
def get_storage() -> LocalStorage:
    """Get singleton LocalStorage instance.

    Returns cached LocalStorage instance. First call creates instance,
    subsequent calls return same instance.

    Returns:
        LocalStorage singleton instance.
    """
    return LocalStorage()

