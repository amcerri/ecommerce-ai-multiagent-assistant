"""
Integration tests for Analytics Agent.

Tests complete Analytics Agent pipeline with real database and dependencies.
"""

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.analytics.agent import AnalyticsAgent
from app.infrastructure.cache.cache_manager import CacheManager
from app.infrastructure.database.repositories.analytics_repo import (
    PostgreSQLAnalyticsRepository,
)
from app.routing.allowlist import AllowlistValidator


class TestAnalyticsAgentIntegration:
    """Integration tests for Analytics Agent."""

    @pytest.mark.asyncio
    async def test_analytics_agent_pipeline(
        self,
        test_db: AsyncSession,
        llm_client_mock: Any,
        cache_mock: Any,
    ) -> None:
        """Test complete Analytics Agent pipeline."""
        # Create repository with real database
        repository = PostgreSQLAnalyticsRepository(test_db)

        # Create allowlist validator
        allowlist_validator = AllowlistValidator()

        # Create cache manager
        cache = CacheManager()
        cache._client = cache_mock

        # Create agent
        agent = AnalyticsAgent(llm_client_mock, repository, allowlist_validator, cache)

        # Create graph state
        class MockState:
            def __init__(self) -> None:
                self.thread_id = "test_thread_789"
                self.query = "How many orders are there?"
                self.language = "pt-BR"
                self.agent_response = None

        state = MockState()

        # Process with agent
        result = await agent.process(state)

        # Verify result
        assert hasattr(result, "agent_response")
        assert result.agent_response is not None
        assert result.agent_response.agent == "analytics"

    @pytest.mark.asyncio
    async def test_analytics_agent_sql_validation(
        self,
        test_db: AsyncSession,
        llm_client_mock: Any,
        cache_mock: Any,
    ) -> None:
        """Test Analytics Agent SQL validation."""
        repository = PostgreSQLAnalyticsRepository(test_db)
        allowlist_validator = AllowlistValidator()
        cache = CacheManager()
        cache._client = cache_mock

        agent = AnalyticsAgent(llm_client_mock, repository, allowlist_validator, cache)

        class MockState:
            def __init__(self) -> None:
                self.thread_id = "test_thread_sql"
                self.query = "Show me all orders"
                self.language = "pt-BR"
                self.agent_response = None

        state = MockState()

        # Process should validate SQL
        result = await agent.process(state)
        assert result.agent_response is not None

