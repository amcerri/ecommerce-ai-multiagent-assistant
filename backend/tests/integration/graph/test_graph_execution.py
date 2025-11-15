"""
Integration tests for graph execution.

Tests complete graph execution flows end-to-end.
"""

from typing import Any

import pytest

from app.graph.build import build_graph
from app.graph.state import GraphState


class TestGraphExecutionIntegration:
    """Integration tests for graph execution."""

    @pytest.mark.asyncio
    async def test_graph_execution_knowledge_route(
        self,
        test_db: Any,
        llm_client_mock: Any,
    ) -> None:
        """Test graph execution routing to knowledge agent."""
        # Build graph
        graph = build_graph(require_sql_approval=False)

        # Create initial state
        initial_state: GraphState = {
            "thread_id": "test_thread_graph_1",
            "query": "What is in the knowledge base?",
            "language": "pt-BR",
            "conversation_history": [],
            "metadata": {},
            "interrupts": {},
        }

        # Execute graph
        result = await graph.ainvoke(initial_state)

        # Verify result
        assert "agent_response" in result
        assert result["agent_response"] is not None
        assert result["agent_response"].agent in ["knowledge", "triage"]

    @pytest.mark.asyncio
    async def test_graph_execution_analytics_route(
        self,
        test_db: Any,
        llm_client_mock: Any,
    ) -> None:
        """Test graph execution routing to analytics agent."""
        graph = build_graph(require_sql_approval=False)

        initial_state: GraphState = {
            "thread_id": "test_thread_graph_2",
            "query": "How many orders are there?",
            "language": "pt-BR",
            "conversation_history": [],
            "metadata": {},
            "interrupts": {},
        }

        result = await graph.ainvoke(initial_state)

        assert "agent_response" in result
        assert result["agent_response"] is not None
        assert result["agent_response"].agent in ["analytics", "triage"]

    @pytest.mark.asyncio
    async def test_graph_execution_triage_fallback(
        self,
        test_db: Any,
        llm_client_mock: Any,
    ) -> None:
        """Test graph execution fallback to triage."""
        graph = build_graph(require_sql_approval=False)

        initial_state: GraphState = {
            "thread_id": "test_thread_graph_3",
            "query": "Hello, how are you?",
            "language": "pt-BR",
            "conversation_history": [],
            "metadata": {},
            "interrupts": {},
        }

        result = await graph.ainvoke(initial_state)

        assert "agent_response" in result
        assert result["agent_response"] is not None
        # Should route to triage for greetings
        assert result["agent_response"].agent == "triage"

    @pytest.mark.asyncio
    async def test_graph_state_persistence(
        self,
        test_db: Any,
        llm_client_mock: Any,
    ) -> None:
        """Test graph state persistence across execution."""
        graph = build_graph(require_sql_approval=False)

        initial_state: GraphState = {
            "thread_id": "test_thread_graph_4",
            "query": "Test query",
            "language": "pt-BR",
            "conversation_history": [],
            "metadata": {},
            "interrupts": {},
        }

        result = await graph.ainvoke(initial_state)

        # Verify state is preserved
        assert result["thread_id"] == initial_state["thread_id"]
        assert result["query"] == initial_state["query"]
        assert result["language"] == initial_state["language"]

    @pytest.mark.asyncio
    async def test_graph_routing_decision(
        self,
        test_db: Any,
        llm_client_mock: Any,
    ) -> None:
        """Test graph routing decision is made correctly."""
        graph = build_graph(require_sql_approval=False)

        initial_state: GraphState = {
            "thread_id": "test_thread_graph_5",
            "query": "Show me analytics data",
            "language": "pt-BR",
            "conversation_history": [],
            "metadata": {},
            "interrupts": {},
        }

        result = await graph.ainvoke(initial_state)

        # Verify routing decision was made
        assert "router_decision" in result
        assert result["router_decision"] is not None
        assert result["router_decision"].agent in ["knowledge", "analytics", "commerce", "triage"]

