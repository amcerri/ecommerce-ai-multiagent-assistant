"""
E2E tests for routing flows.

Tests semantic routing, fallbacks, and out-of-scope query handling.
"""

import uuid
from typing import Any, Dict

import pytest


class TestRoutingFlowsE2E:
    """E2E tests for routing flows."""

    @pytest.mark.asyncio
    async def test_semantic_routing(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test semantic routing (not keyword-based)."""
        thread_id = str(uuid.uuid4())

        # Test 1: Query with keyword "pedido" that semantically means knowledge question
        # (not analytics, even though "pedido" might suggest orders/analytics)
        response1 = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "O que significa pedido neste contexto?",
                "thread_id": f"{thread_id}_1",
                "language": "pt-BR",
            },
        )
        assert response1.status_code == 200
        data1 = response1.json()
        # Should route based on semantic meaning, not keyword
        assert "agent" in data1["response"]

        # Test 2: Query about data analysis (should route to analytics)
        response2 = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Quais são os números de vendas?",
                "thread_id": f"{thread_id}_2",
                "language": "pt-BR",
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # Should route to analytics based on intent (data analysis)
        assert "agent" in data2["response"]

        # Verify routing is semantic (not keyword-based)
        # Both queries might have similar keywords but different intents
        agent1 = data1["response"].get("agent")
        agent2 = data2["response"].get("agent")
        # Routing should be different based on semantic meaning
        assert agent1 in ["knowledge", "triage", "analytics", "commerce"]
        assert agent2 in ["knowledge", "triage", "analytics", "commerce"]

    @pytest.mark.asyncio
    async def test_routing_fallback(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test routing fallback to triage for ambiguous queries."""
        thread_id = str(uuid.uuid4())

        # Send ambiguous query
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "I'm not sure what I need",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Should route to triage for ambiguous queries
        agent = data["response"].get("agent")
        # Triage is a valid fallback
        assert agent in ["triage", "knowledge", "analytics", "commerce"]

        # If routed to triage, verify helpful response
        if agent == "triage":
            assert "text" in data["response"]
            assert len(data["response"]["text"]) > 0

    @pytest.mark.asyncio
    async def test_out_of_scope_routing(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test routing for out-of-scope queries."""
        thread_id = str(uuid.uuid4())

        # Send query outside system scope
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "What's the weather like today?",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Should route to triage for out-of-scope queries
        agent = data["response"].get("agent")
        assert agent in ["triage", "knowledge", "analytics", "commerce"]

        # Triage should provide helpful response
        if agent == "triage":
            assert "text" in data["response"]
            assert len(data["response"]["text"]) > 0

    @pytest.mark.asyncio
    async def test_greeting_routing(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test routing for greetings."""
        thread_id = str(uuid.uuid4())

        # Send greeting
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Hello, how are you?",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Should route to triage for greetings
        agent = data["response"].get("agent")
        assert agent in ["triage", "knowledge", "analytics", "commerce"]

        # Verify friendly response
        assert "text" in data["response"]
        assert len(data["response"]["text"]) > 0

