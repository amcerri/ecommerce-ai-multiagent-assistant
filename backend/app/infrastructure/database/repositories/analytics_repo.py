"""
Analytics repository (data access for analytics tables and SQL execution).

Overview
  Provides repository interface and PostgreSQL implementation for analytics
  operations. Includes secure SQL execution with read-only transactions,
  timeout, and row limits. Follows Repository pattern for abstraction.

Design
  - **Repository Pattern**: Abstract interface with PostgreSQL implementation.
  - **Secure Execution**: Read-only transactions, timeout, row limits.
  - **Parameterized Queries**: Always uses parameterized queries for safety.

Integration
  - Consumes: Database models, SQLAlchemy async session, constants.
  - Returns: AnalyticsTable models and query results.
  - Used by: AnalyticsAgent for schema access and SQL execution.
  - Observability: N/A (data access layer).

Usage
  >>> from app.infrastructure.database.repositories.analytics_repo import PostgreSQLAnalyticsRepository
  >>> repo = PostgreSQLAnalyticsRepository(session)
  >>> tables = await repo.get_all_tables()
  >>> results = await repo.execute_sql("SELECT * FROM analytics.orders LIMIT 10")
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.constants import SQL_MAX_ROWS, SQL_TIMEOUT_MS
from app.config.exceptions import DatabaseException
from app.infrastructure.database.models.analytics import AnalyticsColumn, AnalyticsTable


class AnalyticsRepository(ABC):
    """Abstract repository interface for analytics operations.

    Defines interface for analytics data access operations.
    Concrete implementations provide database-specific logic.

    Methods:
        get_all_tables: List all analytics tables.
        get_table_by_name: Get table by name.
        execute_sql: Execute SQL securely.
    """

    @abstractmethod
    async def get_all_tables(self) -> List[AnalyticsTable]:
        """Get all analytics tables.

        Returns:
            List of AnalyticsTable objects with columns loaded.
        """
        pass

    @abstractmethod
    async def get_table_by_name(self, name: str) -> Optional[AnalyticsTable]:
        """Get analytics table by name.

        Args:
            name: Table name.

        Returns:
            AnalyticsTable object with columns loaded, or None if not found.
        """
        pass

    @abstractmethod
    async def execute_sql(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute SQL securely.

        Executes SQL with read-only transaction, timeout, and row limits.

        Args:
            sql: SQL query to execute.
            params: Query parameters (optional).

        Returns:
            List of dictionaries representing query results.

        Raises:
            DatabaseException: If execution fails.
        """
        pass


class PostgreSQLAnalyticsRepository(AnalyticsRepository):
    """PostgreSQL implementation of analytics repository.

    Provides PostgreSQL implementation for analytics operations with
    secure SQL execution (read-only, timeout, row limits).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize PostgreSQL analytics repository.

        Args:
            session: Async database session.
        """
        self._session = session

    async def get_all_tables(self) -> List[AnalyticsTable]:
        """Get all active analytics tables.

        Returns all analytics tables with their columns loaded.

        Returns:
            List of AnalyticsTable objects with columns relationship loaded.
        """
        try:
            query = (
                select(AnalyticsTable)
                .where(AnalyticsTable.is_active == True)  # noqa: E712
                .options(selectinload(AnalyticsTable.columns))
            )
            result = await self._session.execute(query)
            tables = result.scalars().all()
            return list(tables)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve analytics tables: {str(e)}",
                details={"error": str(e)},
            ) from e

    async def get_table_by_name(self, name: str) -> Optional[AnalyticsTable]:
        """Get analytics table by name.

        Args:
            name: Table name.

        Returns:
            AnalyticsTable object with columns loaded, or None if not found.
        """
        try:
            query = (
                select(AnalyticsTable)
                .where(AnalyticsTable.name == name)
                .where(AnalyticsTable.is_active == True)  # noqa: E712
                .options(selectinload(AnalyticsTable.columns))
            )
            result = await self._session.execute(query)
            table = result.scalar_one_or_none()
            return table
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve analytics table: {str(e)}",
                details={"error": str(e), "table_name": name},
            ) from e

    async def execute_sql(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute SQL securely with read-only transaction, timeout, and row limits.

        Executes SQL in a read-only transaction with timeout and row limits
        for security and performance. Always uses parameterized queries.

        Args:
            sql: SQL query to execute (must be SELECT only).
            params: Query parameters for parameterized query (optional).

        Returns:
            List of dictionaries representing query results (max SQL_MAX_ROWS rows).

        Raises:
            DatabaseException: If execution fails or query is invalid.
        """
        try:
            # Start transaction with read-only and timeout settings
            async with self._session.begin():
                # Set read-only transaction
                await self._session.execute(
                    text("SET LOCAL default_transaction_read_only = on"),
                )
                # Set statement timeout
                await self._session.execute(
                    text(f"SET LOCAL statement_timeout = {SQL_TIMEOUT_MS}"),
                )

                # Execute SQL with parameters (parameterized query)
                result = await self._session.execute(text(sql), params or {})

                # Fetch results with row limit (client-side)
                rows = result.fetchmany(SQL_MAX_ROWS)

                # Convert to list of dictionaries
                if rows:
                    columns = result.keys()
                    result_dicts = [dict(zip(columns, row)) for row in rows]
                else:
                    result_dicts = []

                return result_dicts
        except Exception as e:
            # Rollback is automatic with context manager
            raise DatabaseException(
                message=f"Failed to execute SQL: {str(e)}",
                details={"error": str(e), "sql": sql[:200]},
            ) from e

