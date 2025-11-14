"""
Allowlist validator (SQL query validation against allowed tables/columns).

Overview
  Validates SQL queries against allowlist of allowed tables and columns.
  This is a stub implementation that will be fully implemented in Batch 17.
  For now, provides basic interface for Analytics Agent to use.

Design
  - **Allowlist Validation**: Validates SQL against allowed tables/columns.
  - **Security**: Prevents access to unauthorized tables/columns.
  - **Extensibility**: Easy to extend with function validation.

Integration
  - Consumes: Database models (AnalyticsTable, AnalyticsColumn).
  - Returns: Validation results (boolean or detailed errors).
  - Used by: Analytics Agent for SQL validation.
  - Observability: Logs validation results.

Usage
  >>> from app.routing.allowlist import AllowlistValidator
  >>> validator = AllowlistValidator()
  >>> is_valid = await validator.validate_sql(sql, allowed_tables, allowed_columns)
"""

import logging
from typing import Any, Dict, List, Optional

from app.config.exceptions import ValidationException

logger = logging.getLogger(__name__)


class AllowlistValidator:
    """Allowlist validator for SQL queries.

    Validates SQL queries against allowlist of allowed tables and columns.
    Stub implementation - will be fully implemented in Batch 17.
    """

    def __init__(self) -> None:
        """Initialize allowlist validator.

        Stub implementation - will be fully implemented in Batch 17.
        """
        pass

    async def validate_sql(
        self,
        sql: str,
        allowed_tables: List[str],
        allowed_columns: Optional[Dict[str, List[str]]] = None,
    ) -> bool:
        """Validate SQL against allowlist.

        Validates that SQL query only uses allowed tables and columns.
        Stub implementation - will be fully implemented in Batch 17.

        Args:
            sql: SQL query to validate.
            allowed_tables: List of allowed table names.
            allowed_columns: Dictionary mapping table names to allowed columns (optional).

        Returns:
            True if SQL is valid, False otherwise.

        Raises:
            ValidationException: If SQL uses unauthorized tables/columns.
        """
        # Stub implementation - basic validation
        # Full implementation will be in Batch 17
        sql_upper = sql.upper()

        # Check for dangerous operations
        dangerous_ops = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        for op in dangerous_ops:
            if op in sql_upper:
                raise ValidationException(
                    message=f"SQL contains dangerous operation: {op}",
                    details={"sql": sql[:200], "operation": op},
                )

        # Basic table validation (stub - will be improved in Batch 17)
        # For now, just check that SQL doesn't reference obviously unauthorized tables
        # Full implementation will parse SQL and validate against allowlist

        return True

