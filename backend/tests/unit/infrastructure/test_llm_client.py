"""
Unit tests for LLM client infrastructure.

Tests for app.infrastructure.llm.client.LLMClient interface.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.llm.client import EmbeddingResponse, LLMClient, LLMResponse


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self) -> None:
        """Initialize mock LLM client."""
        self.generate_mock = AsyncMock()
        self.generate_structured_mock = AsyncMock()
        self.generate_embedding_mock = AsyncMock()
        self.generate_embeddings_batch_mock = AsyncMock()

    async def generate(self, prompt: str, **kwargs: dict) -> LLMResponse:
        """Mock generate method."""
        return await self.generate_mock(prompt, **kwargs)

    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
        **kwargs: dict,
    ) -> dict:
        """Mock generate_structured method."""
        return await self.generate_structured_mock(prompt, schema, **kwargs)

    async def generate_embedding(self, text: str) -> EmbeddingResponse:
        """Mock generate_embedding method."""
        return await self.generate_embedding_mock(text)

    async def generate_embeddings_batch(self, texts: list[str]) -> list[EmbeddingResponse]:
        """Mock generate_embeddings_batch method."""
        return await self.generate_embeddings_batch_mock(texts)


class TestLLMClient:
    """Tests for LLMClient interface."""

    @pytest.fixture
    def llm_client(self) -> MockLLMClient:
        """Create mock LLM client."""
        return MockLLMClient()

    @pytest.mark.asyncio
    async def test_generate(self, llm_client: MockLLMClient) -> None:
        """Test generate method."""
        expected_response = LLMResponse(
            text="Test response",
            model="gpt-4",
            tokens_used=10,
        )
        llm_client.generate_mock.return_value = expected_response
        result = await llm_client.generate("Test prompt")
        assert result.text == "Test response"
        assert result.model == "gpt-4"
        llm_client.generate_mock.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_structured(self, llm_client: MockLLMClient) -> None:
        """Test generate_structured method."""
        expected_response = {"key": "value"}
        llm_client.generate_structured_mock.return_value = expected_response
        schema = {"type": "object", "properties": {"key": {"type": "string"}}}
        result = await llm_client.generate_structured("Test prompt", schema)
        assert result == expected_response
        llm_client.generate_structured_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding(self, llm_client: MockLLMClient) -> None:
        """Test generate_embedding method."""
        expected_response = EmbeddingResponse(
            embedding=[0.1] * 1536,
            model="text-embedding-ada-002",
            tokens_used=5,
        )
        llm_client.generate_embedding_mock.return_value = expected_response
        result = await llm_client.generate_embedding("Test text")
        assert len(result.embedding) == 1536
        assert result.model == "text-embedding-ada-002"
        llm_client.generate_embedding_mock.assert_called_once_with("Test text")

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, llm_client: MockLLMClient) -> None:
        """Test generate_embeddings_batch method."""
        expected_responses = [
            EmbeddingResponse(embedding=[0.1] * 1536, model="text-embedding-ada-002"),
            EmbeddingResponse(embedding=[0.2] * 1536, model="text-embedding-ada-002"),
        ]
        llm_client.generate_embeddings_batch_mock.return_value = expected_responses
        texts = ["text1", "text2"]
        result = await llm_client.generate_embeddings_batch(texts)
        assert len(result) == 2
        llm_client.generate_embeddings_batch_mock.assert_called_once_with(texts)

