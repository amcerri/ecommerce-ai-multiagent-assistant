"""
Unit tests for Triage Agent.

Tests for app.agents.triage.agent.TriageAgent.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.triage.agent import TriageAgent
from app.contracts.answer import Answer


class TestTriageAgent:
    """Tests for TriageAgent class."""

    @pytest.fixture
    def llm_client_mock(self) -> MagicMock:
        """Create mock LLM client."""
        mock = MagicMock()
        mock.chat_completion = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": '{"response_type": "greeting", "text": "Hello!", "suggestions": ["Ask about orders"]}',
                        }
                    }
                ],
                "usage": {"total_tokens": 50},
            }
        )
        return mock

    @pytest.fixture
    def agent(self, llm_client_mock: MagicMock) -> TriageAgent:
        """Create TriageAgent instance with mock."""
        return TriageAgent(llm_client_mock)

    @pytest.fixture
    def graph_state(self) -> dict:
        """Create sample graph state."""
        return {
            "thread_id": "test_thread",
            "query": "Hello",
            "language": "pt-BR",
        }

    @pytest.mark.asyncio
    async def test_init(self, agent: TriageAgent) -> None:
        """Test agent initialization."""
        assert agent.name == "triage"
        assert agent.llm_client is not None

    @pytest.mark.asyncio
    async def test_process_success(
        self,
        agent: TriageAgent,
        graph_state: dict,
    ) -> None:
        """Test successful processing."""
        class MockState:
            def __init__(self, data: dict) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        state = MockState(graph_state)
        result = await agent.process(state)
        assert hasattr(result, "agent_response")
        assert isinstance(result.agent_response, Answer)
        assert result.agent_response.agent == "triage"

    @pytest.mark.asyncio
    async def test_process_greeting(
        self,
        agent: TriageAgent,
        graph_state: dict,
    ) -> None:
        """Test processing greeting query."""
        class MockState:
            def __init__(self, data: dict) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        state = MockState({**graph_state, "query": "Hello, how are you?"})
        result = await agent.process(state)
        assert hasattr(result, "agent_response")
        assert result.agent_response.agent == "triage"

