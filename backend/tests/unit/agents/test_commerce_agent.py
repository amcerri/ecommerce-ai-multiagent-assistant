"""
Unit tests for Commerce Agent.

Tests for app.agents.commerce.agent.CommerceAgent.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.commerce.agent import CommerceAgent
from app.contracts.answer import Answer


class TestCommerceAgent:
    """Tests for CommerceAgent class."""

    @pytest.fixture
    def llm_client_mock(self) -> MagicMock:
        """Create mock LLM client."""
        mock = MagicMock()
        mock.generate_structured = AsyncMock(
            return_value={
                "schema": {"fields": ["total", "date"]},
                "extracted_data": {"total": 100.0, "date": "2024-01-01"},
            }
        )
        return mock

    @pytest.fixture
    def storage_mock(self) -> MagicMock:
        """Create mock storage."""
        mock = MagicMock()
        mock.get = AsyncMock(return_value=b"PDF content")
        return mock

    @pytest.fixture
    def repository_mock(self) -> MagicMock:
        """Create mock commerce repository."""
        mock = MagicMock()
        mock.save_document = AsyncMock(return_value="doc_id")
        return mock

    @pytest.fixture
    def agent(
        self,
        llm_client_mock: MagicMock,
        storage_mock: MagicMock,
        repository_mock: MagicMock,
    ) -> CommerceAgent:
        """Create CommerceAgent instance with mocks."""
        return CommerceAgent(llm_client_mock, storage_mock, repository_mock)

    @pytest.fixture
    def graph_state(self) -> dict:
        """Create sample graph state."""
        return {
            "thread_id": "test_thread",
            "query": "Process document",
            "language": "pt-BR",
            "file_path": "test.pdf",
            "file_type": "pdf",
        }

    @pytest.mark.asyncio
    async def test_init(self, agent: CommerceAgent) -> None:
        """Test agent initialization."""
        assert agent.name == "commerce"
        assert agent.llm_client is not None

    @pytest.mark.asyncio
    async def test_process_success(
        self,
        agent: CommerceAgent,
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

    @pytest.mark.asyncio
    async def test_process_missing_file(
        self,
        agent: CommerceAgent,
    ) -> None:
        """Test processing with missing file path."""
        class MockState:
            def __init__(self, data: dict) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        state = MockState({"thread_id": "test", "query": "test"})
        # Should handle missing file_path gracefully
        result = await agent.process(state)
        assert hasattr(result, "agent_response")

