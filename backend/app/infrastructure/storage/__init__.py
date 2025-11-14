"""
Storage module (local file storage system).

Overview
  Provides local file storage system for POC (no cloud costs). Organizes files
  by type and date, generates unique filenames, and validates file types and sizes.
  Implements security validation to prevent path traversal attacks.

Design
  - **Local Storage**: Uses local filesystem (no S3/MinIO for POC).
  - **Organization**: Files organized by type and date (type/YYYY/MM/DD/uuid.ext).
  - **Security**: Validates paths to prevent path traversal attacks.
  - **Validation**: Uses app.utils.validation for file validation.

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

from app.infrastructure.storage.local_storage import LocalStorage, get_storage

__all__ = [
    "LocalStorage",
    "get_storage",
]

