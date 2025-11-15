"""
Unit tests for validation utilities.

Tests for app.utils.validation functions including email, URL,
and file validation.
"""

import pytest

from app.config.exceptions import ValidationException
from app.utils.validation import (
    validate_email,
    validate_file,
    validate_file_size,
    validate_file_type,
    validate_url,
)


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_email(self) -> None:
        """Test valid email addresses."""
        assert validate_email("user@example.com") is True
        assert validate_email("test.user@example.co.uk") is True
        assert validate_email("user+tag@example.com") is True
        assert validate_email("user_name@example-domain.com") is True

    def test_invalid_email(self) -> None:
        """Test invalid email addresses."""
        assert validate_email("invalid") is False
        assert validate_email("invalid@") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user@example") is False
        assert validate_email("user @example.com") is False

    def test_empty_or_none(self) -> None:
        """Test empty or None email."""
        assert validate_email("") is False
        assert validate_email(None) is False  # type: ignore

    def test_email_with_spaces(self) -> None:
        """Test email with leading/trailing spaces."""
        assert validate_email("  user@example.com  ") is True
        assert validate_email(" user@example.com ") is True


class TestValidateURL:
    """Tests for validate_url function."""

    def test_valid_url(self) -> None:
        """Test valid URLs."""
        assert validate_url("http://example.com") is True
        assert validate_url("https://example.com") is True
        assert validate_url("http://example.com/path") is True
        assert validate_url("https://example.com/path/to/page") is True
        assert validate_url("http://subdomain.example.com") is True

    def test_invalid_url(self) -> None:
        """Test invalid URLs."""
        assert validate_url("invalid") is False
        assert validate_url("ftp://example.com") is False
        assert validate_url("example.com") is False
        assert validate_url("http://") is False
        assert validate_url("https://") is False

    def test_empty_or_none(self) -> None:
        """Test empty or None URL."""
        assert validate_url("") is False
        assert validate_url(None) is False  # type: ignore

    def test_url_with_spaces(self) -> None:
        """Test URL with leading/trailing spaces."""
        assert validate_url("  http://example.com  ") is True


class TestValidateFileType:
    """Tests for validate_file_type function."""

    def test_valid_file_types(self) -> None:
        """Test valid file types."""
        assert validate_file_type("document.pdf") is True
        assert validate_file_type("image.jpg") is True
        assert validate_file_type("data.csv") is True
        assert validate_file_type("file.PDF") is True  # Case insensitive
        assert validate_file_type("file.JPG") is True

    def test_invalid_file_types(self) -> None:
        """Test invalid file types."""
        assert validate_file_type("document.exe") is False
        assert validate_file_type("file.bat") is False
        assert validate_file_type("script.sh") is False

    def test_empty_or_none(self) -> None:
        """Test empty or None filename."""
        assert validate_file_type("") is False
        assert validate_file_type(None) is False  # type: ignore

    def test_no_extension(self) -> None:
        """Test filename without extension."""
        assert validate_file_type("filename") is False


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_valid_file_size(self) -> None:
        """Test valid file sizes."""
        assert validate_file_size(0) is True
        assert validate_file_size(1024) is True
        assert validate_file_size(10 * 1024 * 1024) is True  # 10MB

    def test_invalid_file_size(self) -> None:
        """Test invalid file sizes."""
        # Assuming MAX_FILE_SIZE_MB is 10
        assert validate_file_size(11 * 1024 * 1024) is False  # 11MB
        assert validate_file_size(100 * 1024 * 1024) is False  # 100MB

    def test_negative_size(self) -> None:
        """Test negative file size."""
        assert validate_file_size(-1) is False

    def test_invalid_type(self) -> None:
        """Test invalid type for file size."""
        assert validate_file_size(None) is False  # type: ignore
        assert validate_file_size("1024") is False  # type: ignore


class TestValidateFile:
    """Tests for validate_file function."""

    def test_valid_file(self) -> None:
        """Test valid file (type and size)."""
        validate_file("document.pdf", 1024)  # Should not raise

    def test_invalid_file_type(self) -> None:
        """Test invalid file type."""
        with pytest.raises(ValidationException) as exc_info:
            validate_file("document.exe", 1024)
        assert "File type not supported" in str(exc_info.value.message)

    def test_invalid_file_size(self) -> None:
        """Test invalid file size."""
        # Assuming MAX_FILE_SIZE_MB is 10
        with pytest.raises(ValidationException) as exc_info:
            validate_file("document.pdf", 11 * 1024 * 1024)
        assert "File size exceeds" in str(exc_info.value.message)

    def test_invalid_both(self) -> None:
        """Test invalid file type and size."""
        with pytest.raises(ValidationException) as exc_info:
            validate_file("document.exe", 11 * 1024 * 1024)
        # Should raise for file type first
        assert "File type not supported" in str(exc_info.value.message)

