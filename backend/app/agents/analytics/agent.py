"""
Analytics agent (SQL generation and execution orchestrator).

Overview
  Main orchestrator for Analytics Agent pipeline. Coordinates SQL planning,
  execution, and result normalization. Inherits from BaseAgent for common
  functionality (logging, error handling, state validation).

Design
  - **Pipeline Orchestration**: Coordinates plan → execute → normalize pipeline.
  - **Base Agent**: Inherits from BaseAgent for common functionality.
  - **Dependency Injection**: Receives dependencies via constructor.
  - **Error Handling**: Uses BaseAgent error handling.

Integration
  - Consumes: BaseAgent, AnalyticsPlanner, AnalyticsExecutor, AnalyticsNormalizer.
  - Returns: Updated GraphState with Answer containing SQLMetadata.
  - Used by: LangGraph orchestration layer.
  - Observability: Logs via BaseAgent._log_processing.

Usage
  >>> from app.agents.analytics.agent import AnalyticsAgent
  >>> agent = AnalyticsAgent(llm_client, repository, allowlist_validator, cache)
  >>> state = await agent.process(state)
"""

import time
from typing import Any, Optional

from app.agents.analytics.executor import AnalyticsExecutor
from app.agents.analytics.normalizer import AnalyticsNormalizer
from app.agents.analytics.planner import AnalyticsPlanner
from app.agents.base import BaseAgent
from app.contracts.answer import Answer, PerformanceMetrics, SQLMetadata
from app.infrastructure.cache.cache_manager import CacheManager
from app.infrastructure.database.repositories.analytics_repo import AnalyticsRepository
from app.infrastructure.llm.client import LLMClient
from app.routing.allowlist import AllowlistValidator


class AnalyticsAgent(BaseAgent):
    """Analytics Agent with SQL generation and execution pipeline.

    Orchestrates SQL planning, execution, and result normalization for
    analytics queries. Inherits from BaseAgent for common functionality.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        repository: AnalyticsRepository,
        allowlist_validator: AllowlistValidator,
        cache: Optional[CacheManager] = None,
    ) -> None:
        """Initialize Analytics Agent.

        Creates planner, executor, and normalizer instances with dependencies.

        Args:
            llm_client: LLM client for SQL generation.
            repository: Analytics repository for schema access and SQL execution.
            allowlist_validator: Allowlist validator for SQL validation.
            cache: Cache manager for SQL caching (optional).
        """
        super().__init__(llm_client, name="analytics")

        # Create pipeline components
        self._planner = AnalyticsPlanner(llm_client, allowlist_validator, cache)
        self._executor = AnalyticsExecutor(repository)
        self._normalizer = AnalyticsNormalizer(llm_client)
        self._repository = repository

    async def process(self, state: Any) -> Any:
        """Process query and generate answer.

        Implements abstract method from BaseAgent. Orchestrates pipeline:
        plan → execute → normalize. Updates state with Answer.

        Args:
            state: Graph state with query, language, etc.

        Returns:
            Updated state with agent_response containing Answer.
        """
        # Step 1: Validate state
        self._validate_state(state)

        total_start_time = time.time()

        try:
            # Extract query and language from state
            query = getattr(state, "query", "")
            language = getattr(state, "language", "pt-BR")

            # Step 2: Get schema info
            schema_info = await self._get_schema_info()

            # Step 3: Plan SQL
            plan_start = time.time()
            plan_result = await self._planner.plan(query, schema_info, language)
            plan_time = (time.time() - plan_start) * 1000

            sql = plan_result["sql"]
            explanation = plan_result["explanation"]
            tables_used = plan_result["tables_used"]
            columns_used = plan_result["columns_used"]
            confidence = plan_result["confidence"]

            # Step 4: Execute SQL
            exec_start = time.time()
            exec_result = await self._executor.execute(sql)
            exec_time = (time.time() - exec_start) * 1000

            rows = exec_result["rows"]
            row_count = exec_result["row_count"]
            execution_time_ms = exec_result["execution_time_ms"]
            query_plan = exec_result.get("query_plan")

            # Step 5: Normalize results
            normalize_start = time.time()
            normalized = await self._normalizer.normalize(rows, sql, language)
            normalize_time = (time.time() - normalize_start) * 1000

            # Step 6: Build answer text
            answer_text = self._build_answer_text(
                normalized,
                explanation,
                row_count,
                language,
            )

            # Step 7: Create SQLMetadata
            sql_metadata = SQLMetadata(
                sql=sql,
                explanation=explanation,
                tables_used=tables_used,
                columns_used=columns_used,
                execution_time_ms=execution_time_ms,
                rows_returned=row_count,
                query_plan=query_plan,
            )

            # Step 8: Create PerformanceMetrics
            total_time_ms = (time.time() - total_start_time) * 1000
            performance_metrics = PerformanceMetrics(
                total_time_ms=total_time_ms,
                retrieval_time_ms=None,
                generation_time_ms=plan_time,
                tokens_used=None,  # Could be extracted from LLM response
                cost_estimate=None,
            )

            # Step 9: Create Answer
            answer = Answer(
                text=answer_text,
                agent="analytics",
                language=language,
                sql_metadata=sql_metadata,
                performance_metrics=performance_metrics,
            )

            # Step 10: Update state
            if hasattr(state, "agent_response"):
                state.agent_response = answer
            else:
                setattr(state, "agent_response", answer)

            # Step 11: Log processing
            await self._log_processing(state, answer)

            return state
        except Exception as e:
            # Use BaseAgent error handling
            return await self._handle_error(e, state)

    async def _get_schema_info(self) -> dict[str, Any]:
        """Get schema information for SQL planning.

        Retrieves all analytics tables and their columns to provide
        schema information for SQL generation.

        Returns:
            Dictionary with schema information (tables, columns, types).
        """
        try:
            tables = await self._repository.get_all_tables()

            schema_tables: list[dict[str, Any]] = []
            for table in tables:
                table_info: dict[str, Any] = {
                    "name": table.name,
                    "description": table.description,
                    "columns": [],
                }

                for column in table.columns:
                    column_info: dict[str, Any] = {
                        "name": column.name,
                        "data_type": column.data_type,
                        "is_nullable": column.is_nullable,
                        "is_primary_key": column.is_primary_key,
                        "is_foreign_key": column.is_foreign_key,
                    }
                    table_info["columns"].append(column_info)

                schema_tables.append(table_info)

            return {"tables": schema_tables}
        except Exception as e:
            # Return empty schema if retrieval fails
            self.logger.warning(f"Failed to retrieve schema info: {e}")
            return {"tables": []}

    def _build_answer_text(
        self,
        normalized: dict[str, Any],
        explanation: str,
        row_count: int,
        language: str,
    ) -> str:
        """Build answer text from normalized results.

        Constructs human-readable answer text from normalized results
        and SQL explanation.

        Args:
            normalized: Normalized results with formatted data and summary.
            explanation: SQL explanation.
            row_count: Number of rows returned.

        Returns:
            Formatted answer text.
        """
        if language.startswith("pt"):
            answer_parts: list[str] = [
                f"Encontrei {row_count} resultado(s).",
            ]

            if explanation:
                answer_parts.append(f"\n{explanation}")

            # Add insights if available
            insights = normalized.get("insights")
            if insights and insights.get("descriptive"):
                answer_parts.append(f"\n\nInsights:\n{insights['descriptive']}")

            return "\n".join(answer_parts)
        else:
            answer_parts = [
                f"Found {row_count} result(s).",
            ]

            if explanation:
                answer_parts.append(f"\n{explanation}")

            # Add insights if available
            insights = normalized.get("insights")
            if insights and insights.get("descriptive"):
                answer_parts.append(f"\n\nInsights:\n{insights['descriptive']}")

            return "\n".join(answer_parts)

