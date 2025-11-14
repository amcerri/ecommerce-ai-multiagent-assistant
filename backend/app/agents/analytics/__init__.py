"""
Analytics agent module (SQL generation and execution pipeline).

Overview
  Provides complete SQL generation and execution pipeline for analytics queries
  including planning, execution, normalization, and schema building. Main entry
  point is AnalyticsAgent which orchestrates the pipeline.

Design
  - **SQL Pipeline**: Planning → Execution → Normalization.
  - **Modular Components**: Separate classes for each pipeline step.
  - **Base Agent**: AnalyticsAgent inherits from BaseAgent.
  - **Repository Pattern**: Uses AnalyticsRepository for data access.
  - **Secure Execution**: Read-only transactions, timeout, row limits.

Integration
  - Consumes: BaseAgent, LLMClient, AnalyticsRepository, AllowlistValidator, CacheManager.
  - Returns: Answer objects with SQLMetadata and formatted results.
  - Used by: LangGraph orchestration, administrative scripts (schema_builder).
  - Observability: Logs via BaseAgent and individual components.

Usage
  >>> from app.agents.analytics import AnalyticsAgent
  >>> agent = AnalyticsAgent(llm_client, repository, allowlist_validator, cache)
  >>> state = await agent.process(state)
"""

from app.agents.analytics.agent import AnalyticsAgent
from app.agents.analytics.executor import AnalyticsExecutor
from app.agents.analytics.normalizer import AnalyticsNormalizer
from app.agents.analytics.planner import AnalyticsPlanner
from app.agents.analytics.schema_builder import AnalyticsSchemaBuilder

__all__ = [
    "AnalyticsAgent",
    "AnalyticsPlanner",
    "AnalyticsExecutor",
    "AnalyticsNormalizer",
    "AnalyticsSchemaBuilder",
]

