"""
Unit tests for Knowledge Agent.

Tests for app.agents.knowledge.agent.KnowledgeAgent.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.knowledge.agent import KnowledgeAgent
from app.contracts.answer import Answer
from app.infrastructure.database.models.knowledge import DocumentChunk


class TestKnowledgeAgent:
    """Tests for KnowledgeAgent class."""

    @pytest.fixture
    def llm_client_mock(self) -> MagicMock:
        """Create mock LLM client."""
        mock = MagicMock()
        mock.generate_embedding = AsyncMock(
            return_value={"embedding": [0.1] * 1536, "model": "text-embedding-ada-002"}
        )
        mock.chat_completion = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": "Answer text with [1] citations.",
                        }
                    }
                ],
                "usage": {"total_tokens": 100},
            }
        )
        return mock

    @pytest.fixture
    def repository_mock(self) -> MagicMock:
        """Create mock knowledge repository."""
        mock = MagicMock()
        chunk = DocumentChunk(
            id="chunk_1",
            document_id="doc_1",
            content="Test content",
            chunk_index=0,
            embedding=[0.1] * 1536,
        )
        mock.get_chunks_by_embedding = AsyncMock(return_value=[chunk])
        return mock

    @pytest.fixture
    def agent(
        self,
        llm_client_mock: MagicMock,
        repository_mock: MagicMock,
        cache_mock: MagicMock,
    ) -> KnowledgeAgent:
        """Create KnowledgeAgent instance with mocks."""
        return KnowledgeAgent(llm_client_mock, repository_mock, cache_mock)

    @pytest.fixture
    def graph_state(self) -> dict:
        """Create sample graph state."""
        return {
            "thread_id": "test_thread",
            "query": "Test query",
            "language": "pt-BR",
        }

    @pytest.mark.asyncio
    async def test_init(self, agent: KnowledgeAgent) -> None:
        """Test agent initialization."""
        assert agent.name == "knowledge"
        assert agent.llm_client is not None

    @pytest.mark.asyncio
    async def test_process_success(
        self,
        agent: KnowledgeAgent,
        graph_state: dict,
    ) -> None:
        """Test successful processing."""
        # Create a mock state object
        class MockState:
            def __init__(self, data: dict) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        state = MockState(graph_state)
        result = await agent.process(state)
        assert hasattr(result, "agent_response")
        assert isinstance(result.agent_response, Answer)

    @pytest.mark.asyncio
    async def test_process_with_error(
        self,
        agent: KnowledgeAgent,
        graph_state: dict,
        repository_mock: MagicMock,
    ) -> None:
        """Test processing with error."""
        repository_mock.get_chunks_by_embedding = AsyncMock(side_effect=Exception("DB error"))
        class MockState:
            def __init__(self, data: dict) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        state = MockState(graph_state)
        result = await agent.process(state)
        # Should handle error gracefully
        assert hasattr(result, "agent_response")

    @pytest.mark.asyncio
    async def test_validate_state(
        self,
        agent: KnowledgeAgent,
    ) -> None:
        """Test state validation."""
        class MockState:
            def __init__(self, data: dict) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        # Valid state
        valid_state = MockState({"thread_id": "test", "query": "test"})
        # Should not raise
        agent._validate_state(valid_state)

        # Invalid state (missing query)
        invalid_state = MockState({"thread_id": "test"})
        with pytest.raises(Exception):  # Should raise ValidationException
            agent._validate_state(invalid_state)

