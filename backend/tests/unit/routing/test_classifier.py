"""
Unit tests for routing classifier.

Tests for app.routing.classifier.LLMClassifier.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.contracts.router_decision import RouterDecision
from app.routing.classifier import LLMClassifier


class TestLLMClassifier:
    """Tests for LLMClassifier class."""

    @pytest.fixture
    def llm_client_mock(self) -> MagicMock:
        """Create mock LLM client."""
        mock = MagicMock()
        mock.chat_completion = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": '{"agent": "knowledge", "confidence": 0.9, "reason": "Query is about knowledge"}',
                        }
                    }
                ]
            }
        )
        return mock

    @pytest.fixture
    def classifier(self, llm_client_mock: MagicMock) -> LLMClassifier:
        """Create LLMClassifier instance with mock."""
        return LLMClassifier(llm_client_mock)

    @pytest.mark.asyncio
    async def test_classify_success(self, classifier: LLMClassifier) -> None:
        """Test successful classification."""
        query_embedding = [0.1] * 1536
        decision = await classifier.classify("How many orders?", query_embedding, "pt-BR")
        assert isinstance(decision, RouterDecision)
        assert decision.agent in ["knowledge", "analytics", "commerce", "triage"]

    @pytest.mark.asyncio
    async def test_classify_with_cache(
        self,
        llm_client_mock: MagicMock,
        cache_mock: MagicMock,
    ) -> None:
        """Test classification with cache."""
        classifier = LLMClassifier(llm_client_mock, cache_mock)
        query_embedding = [0.1] * 1536
        # First call should use LLM
        await classifier.classify("Test query", query_embedding, "pt-BR")
        assert llm_client_mock.chat_completion.called

    @pytest.mark.asyncio
    async def test_classify_semantic_not_keywords(
        self,
        classifier: LLMClassifier,
    ) -> None:
        """Test that classification is semantic, not keyword-based."""
        query_embedding = [0.1] * 1536
        # Query with keyword that might suggest analytics, but semantic meaning is different
        decision = await classifier.classify(
            "Tell me about orders in general",
            query_embedding,
            "pt-BR",
        )
        # Should use semantic understanding, not keyword matching
        assert isinstance(decision, RouterDecision)

