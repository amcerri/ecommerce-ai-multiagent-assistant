"""
Analytics executor (secure SQL execution).

Overview
  Executes SQL queries securely with read-only transactions, timeout,
  and row limits. Measures execution time and optionally provides query plans.

Design
  - **Secure Execution**: Always via repository (read-only, timeout, row limit).
  - **Performance Measurement**: Tracks execution time.
  - **Query Plans**: Optional query plan generation for analysis.

Integration
  - Consumes: AnalyticsRepository, constants.
  - Returns: Query results with metadata (rows, count, time, plan).
  - Used by: AnalyticsAgent for SQL execution.
  - Observability: Logs execution time and results.

Usage
  >>> from app.agents.analytics.executor import AnalyticsExecutor
  >>> executor = AnalyticsExecutor(repository)
  >>> result = await executor.execute("SELECT * FROM analytics.orders LIMIT 10")
"""

import time
from typing import Any, Dict, List, Optional

from app.config.exceptions import DatabaseException
from app.infrastructure.database.repositories.analytics_repo import AnalyticsRepository


class AnalyticsExecutor:
    """SQL executor for analytics queries.

    Executes SQL queries securely via repository with performance measurement
    and optional query plan generation.
    """

    def __init__(self, repository: AnalyticsRepository) -> None:
        """Initialize analytics executor.

        Args:
            repository: Analytics repository for SQL execution.
        """
        self._repository = repository

    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute SQL query securely.

        Executes SQL via repository (which implements read-only, timeout,
        row limits) and measures execution time.

        Args:
            sql: SQL query to execute (already validated).
            params: Query parameters (optional).

        Returns:
            Dictionary with rows, row_count, execution_time_ms, query_plan (optional).

        Raises:
            DatabaseException: If execution fails.
        """
        # Measure execution time
        start_time = time.time()

        try:
            # Execute SQL via repository (already implements security)
            rows = await self._repository.execute_sql(sql, params)

            # Measure execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Get query plan (optional, for analysis)
            query_plan = None
            try:
                query_plan = await self.explain(sql)
            except Exception:
                # Graceful degradation: continue without query plan
                pass

            return {
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": execution_time_ms,
                "query_plan": query_plan,
            }
        except DatabaseException:
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to execute SQL: {str(e)}",
                details={"sql": sql[:200], "error": str(e)},
            ) from e

    async def explain(self, sql: str) -> Optional[Dict[str, Any]]:
        """Get query execution plan.

        Executes EXPLAIN ANALYZE to get query execution plan without
        executing the actual query.

        Args:
            sql: SQL query to explain.

        Returns:
            Query plan dictionary, or None if unavailable.

        Raises:
            DatabaseException: If explain fails.
        """
        try:
            explain_sql = f"EXPLAIN (FORMAT JSON) {sql}"
            result = await self._repository.execute_sql(explain_sql)

            if result and len(result) > 0:
                # EXPLAIN returns JSON in first row
                plan_data = result[0].get("QUERY PLAN", {})
                if isinstance(plan_data, str):
                    import json

                    plan_data = json.loads(plan_data)
                return plan_data

            return None
        except Exception as e:
            # Graceful degradation: return None if explain fails
            return None

