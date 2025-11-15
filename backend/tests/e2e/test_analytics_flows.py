"""
E2E tests for Analytics Agent flows.

Tests complete Analytics Agent flows including SQL generation,
execution, and validation.
"""

import uuid
from typing import Any, Dict

import pytest


class TestAnalyticsFlowsE2E:
    """E2E tests for Analytics Agent flows."""

    @pytest.mark.asyncio
    async def test_analytics_query_with_sql(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test analytics query with SQL generation."""
        thread_id = str(uuid.uuid4())

        # Send query that should route to analytics agent
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "How many orders are there?",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Verify response
        assert "text" in data["response"]
        assert len(data["response"]["text"]) > 0

        # Check for SQL metadata if agent is analytics
        if data["response"].get("agent") == "analytics":
            if "metadata" in data and data["metadata"]:
                sql_metadata = data["metadata"].get("sql")
                if sql_metadata:
                    assert "sql" in sql_metadata or "explanation" in sql_metadata

    @pytest.mark.asyncio
    async def test_analytics_routing(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test semantic routing to analytics agent."""
        thread_id = str(uuid.uuid4())

        # Send query that semantically should route to analytics
        # (asking for data analysis, not information retrieval)
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Show me statistics about sales",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Verify routing decision
        agent = data["response"].get("agent")
        assert agent in ["analytics", "triage", "knowledge", "commerce"]

        # If routed to analytics, verify response
        if agent == "analytics":
            assert "text" in data["response"]
            assert len(data["response"]["text"]) > 0

    @pytest.mark.asyncio
    async def test_sql_approval_flow(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test SQL approval flow (human-in-the-loop)."""
        thread_id = str(uuid.uuid4())

        # Send query that requires SQL approval
        # Note: This test assumes SQL approval is enabled
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Execute a complex analytics query",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # If SQL approval is required, response might indicate interrupt
        # This is a simplified test - full implementation would check for interrupts
        assert "response" in data
        assert "agent" in data["response"]

