"""
Unit tests for allowlist validator.

Tests for app.routing.allowlist.AllowlistValidator.
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.config.exceptions import ValidationException
from app.routing.allowlist import AllowlistValidator


class TestAllowlistValidator:
    """Tests for AllowlistValidator class."""

    @pytest.fixture
    def allowlist_file(self) -> Path:
        """Create temporary allowlist file."""
        allowlist = {
            "tables": {
                "orders": {"allowed": True, "columns": ["id", "total", "date"]},
                "users": {"allowed": True, "columns": ["id", "name", "email"]},
            },
            "functions": ["COUNT", "SUM", "AVG", "MAX", "MIN"],
            "operators": ["=", "!=", ">", "<", ">=", "<=", "AND", "OR"],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(allowlist, f)
            yield Path(f.name)
        Path(f.name).unlink()

    @pytest.fixture
    def validator(self, allowlist_file: Path) -> AllowlistValidator:
        """Create AllowlistValidator instance."""
        return AllowlistValidator(allowlist_file)

    def test_init(self, validator: AllowlistValidator) -> None:
        """Test validator initialization."""
        assert validator is not None
        assert validator.get_allowed_tables() == ["orders", "users"]

    def test_validate_sql_allowed(self, validator: AllowlistValidator) -> None:
        """Test validation of allowed SQL."""
        # Should not raise
        validator.validate_sql("SELECT * FROM orders LIMIT 10")

    def test_validate_sql_dangerous_operation(self, validator: AllowlistValidator) -> None:
        """Test validation blocks dangerous operations."""
        with pytest.raises(ValidationException) as exc_info:
            validator.validate_sql("DROP TABLE orders")
        assert "dangerous operation" in str(exc_info.value.message).lower()

    def test_validate_sql_delete(self, validator: AllowlistValidator) -> None:
        """Test validation blocks DELETE."""
        with pytest.raises(ValidationException):
            validator.validate_sql("DELETE FROM orders")

    def test_validate_sql_empty(self, validator: AllowlistValidator) -> None:
        """Test validation of empty SQL."""
        with pytest.raises(ValidationException):
            validator.validate_sql("")

    def test_get_allowed_tables(self, validator: AllowlistValidator) -> None:
        """Test getting allowed tables."""
        tables = validator.get_allowed_tables()
        assert "orders" in tables
        assert "users" in tables

    def test_get_allowed_columns(self, validator: AllowlistValidator) -> None:
        """Test getting allowed columns for table."""
        columns = validator.get_allowed_columns("orders")
        assert "id" in columns
        assert "total" in columns
        assert "date" in columns

    def test_get_allowed_columns_nonexistent_table(
        self,
        validator: AllowlistValidator,
    ) -> None:
        """Test getting columns for nonexistent table."""
        columns = validator.get_allowed_columns("nonexistent")
        assert columns == []

