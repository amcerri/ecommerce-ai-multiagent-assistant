"""
Unit tests for routing.

Tests for app.routing.router.Router.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.contracts.router_decision import RouterDecision
from app.routing.classifier import LLMClassifier
from app.routing.router import Router


class TestRouter:
    """Tests for Router class."""

    @pytest.fixture
    def llm_client_mock(self) -> MagicMock:
        """Create mock LLM client."""
        mock = MagicMock()
        mock.generate_embedding = AsyncMock(
            return_value={"embedding": [0.1] * 1536, "model": "text-embedding-ada-002"}
        )
        return mock

    @pytest.fixture
    def classifier_mock(self) -> MagicMock:
        """Create mock classifier."""
        mock = MagicMock(spec=LLMClassifier)
        decision = RouterDecision(
            agent="knowledge",
            confidence=0.9,
            reason="Query is about knowledge base",
        )
        mock.classify = AsyncMock(return_value=decision)
        return mock

    @pytest.fixture
    def router(self, llm_client_mock: MagicMock, classifier_mock: MagicMock) -> Router:
        """Create Router instance with mocks."""
        return Router(llm_client_mock, classifier_mock)

    @pytest.mark.asyncio
    async def test_route_success(self, router: Router) -> None:
        """Test successful routing."""
        decision = await router.route("How many orders?", "pt-BR")
        assert decision.agent == "knowledge"
        assert decision.confidence == 0.9

    @pytest.mark.asyncio
    async def test_route_with_cache(self, router: Router, llm_client_mock: MagicMock) -> None:
        """Test routing with cache."""
        # First call should generate embedding
        await router.route("How many orders?", "pt-BR")
        assert llm_client_mock.generate_embedding.called

    @pytest.mark.asyncio
    async def test_route_fallback_to_triage(
        self,
        llm_client_mock: MagicMock,
        classifier_mock: MagicMock,
    ) -> None:
        """Test fallback to triage on error."""
        classifier_mock.classify = AsyncMock(side_effect=Exception("Classification failed"))
        router = Router(llm_client_mock, classifier_mock)
        decision = await router.route("Test query", "pt-BR")
        # Should fallback to triage
        assert decision.agent == "triage"

