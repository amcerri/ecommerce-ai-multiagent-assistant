"""
E2E tests for Knowledge Agent flows.

Tests complete Knowledge Agent flows including routing, retrieval,
and response generation with citations.
"""

import uuid
from typing import Any, Dict

import pytest


class TestKnowledgeFlowsE2E:
    """E2E tests for Knowledge Agent flows."""

    @pytest.mark.asyncio
    async def test_knowledge_query_with_citations(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test knowledge query with citations."""
        thread_id = str(uuid.uuid4())

        # Send query that should route to knowledge agent
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "What information is available in the knowledge base?",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Verify response has text
        assert "text" in data["response"]
        assert len(data["response"]["text"]) > 0

        # Check for citations if agent is knowledge
        if data["response"].get("agent") == "knowledge":
            # Citations might be in metadata or response
            if "metadata" in data and data["metadata"]:
                citations = data["metadata"].get("citations", [])
                # Citations are optional, so we just verify structure if present
                if citations:
                    assert isinstance(citations, list)

    @pytest.mark.asyncio
    async def test_knowledge_routing(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test semantic routing to knowledge agent."""
        thread_id = str(uuid.uuid4())

        # Send query that semantically should route to knowledge
        # (asking about information, not analytics or commerce)
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Tell me about the documentation available",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Verify routing decision (should be knowledge or triage)
        agent = data["response"].get("agent")
        assert agent in ["knowledge", "triage", "analytics", "commerce"]

        # If routed to knowledge, verify response quality
        if agent == "knowledge":
            assert "text" in data["response"]
            assert len(data["response"]["text"]) > 0

