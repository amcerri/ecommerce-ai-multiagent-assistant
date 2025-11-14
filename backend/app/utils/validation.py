"""
Validation utilities (data validation functions).

Overview
  Provides utility functions for validating common data types including
  email addresses, URLs, and file properties (type and size). All validation
  functions use constants from app.config.constants for configuration values.

Design
  - **Pure Functions**: All validation functions are pure (no side effects).
  - **Constants-Based**: Uses constants from app.config.constants (no hardcoded values).
  - **Exception Handling**: validate_file raises ValidationException on failure.
  - **Type Safety**: All functions use type hints for parameters and return values.

Integration
  - Consumes: app.config.constants, app.config.exceptions.
  - Returns: Boolean validation results or raises exceptions.
  - Used by: All modules that need to validate user input or file uploads.
  - Observability: N/A (pure validation functions).

Usage
  >>> from app.utils.validation import validate_email, validate_file
  >>> is_valid = validate_email("user@example.com")
  >>> validate_file("document.pdf", 1024 * 1024)  # Raises ValidationException if invalid
"""

import re
from pathlib import Path

from app.config.constants import MAX_FILE_SIZE_MB, SUPPORTED_FILE_TYPES
from app.config.exceptions import ValidationException

# Email validation regex pattern
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    re.IGNORECASE,
)

# URL validation regex pattern (HTTP/HTTPS)
URL_PATTERN = re.compile(
    r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/.*)?$",
    re.IGNORECASE,
)


def validate_email(email: str) -> bool:
    """Validate email address format.

    Validates email address using regex pattern. Returns False for
    empty strings, None, or invalid formats.

    Args:
        email: Email address string to validate.

    Returns:
        True if email format is valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_url(url: str) -> bool:
    """Validate URL format (HTTP/HTTPS).

    Validates URL format using regex pattern for HTTP/HTTPS URLs.
    Returns False for empty strings, None, or invalid formats.

    Args:
        url: URL string to validate.

    Returns:
        True if URL format is valid, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    return bool(URL_PATTERN.match(url.strip()))


def validate_file_type(filename: str) -> bool:
    """Validate file type against supported file types.

    Extracts file extension and checks if it's in the list of
    supported file types from app.config.constants.

    Args:
        filename: Filename with extension to validate.

    Returns:
        True if file type is supported, False otherwise.
    """
    if not filename or not isinstance(filename, str):
        return False

    try:
        extension = Path(filename).suffix.lstrip(".").lower()
        return extension in SUPPORTED_FILE_TYPES
    except (AttributeError, ValueError):
        return False


def validate_file_size(file_size_bytes: int) -> bool:
    """Validate file size against maximum allowed size.

    Compares file size in bytes against maximum file size from
    app.config.constants (MAX_FILE_SIZE_MB).

    Args:
        file_size_bytes: File size in bytes to validate.

    Returns:
        True if file size is within limit, False otherwise.
    """
    if not isinstance(file_size_bytes, int) or file_size_bytes < 0:
        return False

    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size_bytes <= max_size_bytes


def validate_file(filename: str, file_size_bytes: int) -> None:
    """Validate file (type and size) and raise exception if invalid.

    Validates both file type and file size. Raises ValidationException
    with descriptive message if either validation fails.

    Args:
        filename: Filename with extension to validate.
        file_size_bytes: File size in bytes to validate.

    Raises:
        ValidationException: If file type or size is invalid.
    """
    if not validate_file_type(filename):
        raise ValidationException(
            message=f"File type not supported. Supported types: {', '.join(SUPPORTED_FILE_TYPES)}",
            details={"filename": filename},
        )

    if not validate_file_size(file_size_bytes):
        max_size_mb = MAX_FILE_SIZE_MB
        raise ValidationException(
            message=f"File size exceeds maximum allowed size of {max_size_mb}MB",
            details={
                "filename": filename,
                "file_size_bytes": file_size_bytes,
                "max_size_bytes": max_size_mb * 1024 * 1024,
            },
        )

