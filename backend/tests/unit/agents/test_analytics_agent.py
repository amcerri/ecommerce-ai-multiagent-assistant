"""
Unit tests for Analytics Agent.

Tests for app.agents.analytics.agent.AnalyticsAgent.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.analytics.agent import AnalyticsAgent
from app.contracts.answer import Answer


class TestAnalyticsAgent:
    """Tests for AnalyticsAgent class."""

    @pytest.fixture
    def llm_client_mock(self) -> MagicMock:
        """Create mock LLM client."""
        mock = MagicMock()
        mock.generate_structured = AsyncMock(
            return_value={
                "sql": "SELECT COUNT(*) FROM orders",
                "explanation": "Count orders",
            }
        )
        return mock

    @pytest.fixture
    def repository_mock(self) -> MagicMock:
        """Create mock analytics repository."""
        mock = MagicMock()
        mock.get_schema_info = AsyncMock(return_value={"tables": ["orders"]})
        mock.execute_sql = AsyncMock(return_value=[{"count": 10}])
        return mock

    @pytest.fixture
    def allowlist_validator_mock(self) -> MagicMock:
        """Create mock allowlist validator."""
        mock = MagicMock()
        mock.validate_sql = MagicMock()  # No exception means valid
        return mock

    @pytest.fixture
    def agent(
        self,
        llm_client_mock: MagicMock,
        repository_mock: MagicMock,
        allowlist_validator_mock: MagicMock,
        cache_mock: MagicMock,
    ) -> AnalyticsAgent:
        """Create AnalyticsAgent instance with mocks."""
        return AnalyticsAgent(
            llm_client_mock,
            repository_mock,
            allowlist_validator_mock,
            cache_mock,
        )

    @pytest.fixture
    def graph_state(self) -> dict:
        """Create sample graph state."""
        return {
            "thread_id": "test_thread",
            "query": "How many orders?",
            "language": "pt-BR",
        }

    @pytest.mark.asyncio
    async def test_init(self, agent: AnalyticsAgent) -> None:
        """Test agent initialization."""
        assert agent.name == "analytics"
        assert agent.llm_client is not None

    @pytest.mark.asyncio
    async def test_process_success(
        self,
        agent: AnalyticsAgent,
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
    async def test_process_with_sql_validation(
        self,
        agent: AnalyticsAgent,
        graph_state: dict,
        allowlist_validator_mock: MagicMock,
    ) -> None:
        """Test processing with SQL validation."""
        class MockState:
            def __init__(self, data: dict) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        state = MockState(graph_state)
        await agent.process(state)
        # Should validate SQL
        allowlist_validator_mock.validate_sql.assert_called()

