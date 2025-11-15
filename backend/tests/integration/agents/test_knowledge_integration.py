"""
Integration tests for Knowledge Agent.

Tests complete Knowledge Agent pipeline with real database and dependencies.
"""

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.knowledge.agent import KnowledgeAgent
from app.infrastructure.cache.cache_manager import CacheManager
from app.infrastructure.database.models.knowledge import Document, DocumentChunk
from app.infrastructure.database.repositories.knowledge_repo import (
    PostgreSQLKnowledgeRepository,
)


class TestKnowledgeAgentIntegration:
    """Integration tests for Knowledge Agent."""

    @pytest.mark.asyncio
    async def test_knowledge_agent_pipeline(
        self,
        test_db: AsyncSession,
        llm_client_mock: Any,
        cache_mock: Any,
    ) -> None:
        """Test complete Knowledge Agent pipeline."""
        # Create repository with real database
        repository = PostgreSQLKnowledgeRepository(test_db)

        # Create cache manager (using mock for now)
        cache = CacheManager()
        cache._client = cache_mock

        # Create agent
        agent = KnowledgeAgent(llm_client_mock, repository, cache)

        # Create test document and chunk
        document = Document(
            id="test_doc_1",
            title="Test Document",
            file_name="test.pdf",
            file_path="test/test.pdf",
            file_type="pdf",
            metadata={},
        )
        chunk = DocumentChunk(
            id="test_chunk_1",
            document_id="test_doc_1",
            content="This is test content about orders and products.",
            chunk_index=0,
            embedding=[0.1] * 1536,
        )

        # Save to database
        test_db.add(document)
        test_db.add(chunk)
        await test_db.commit()

        # Create graph state
        class MockState:
            def __init__(self) -> None:
                self.thread_id = "test_thread_123"
                self.query = "What is this document about?"
                self.language = "pt-BR"
                self.agent_response = None

        state = MockState()

        # Process with agent
        result = await agent.process(state)

        # Verify result
        assert hasattr(result, "agent_response")
        assert result.agent_response is not None
        assert result.agent_response.agent == "knowledge"
        assert result.agent_response.text is not None

    @pytest.mark.asyncio
    async def test_knowledge_agent_with_cache(
        self,
        test_db: AsyncSession,
        llm_client_mock: Any,
        cache_mock: Any,
    ) -> None:
        """Test Knowledge Agent with caching."""
        repository = PostgreSQLKnowledgeRepository(test_db)
        cache = CacheManager()
        cache._client = cache_mock

        agent = KnowledgeAgent(llm_client_mock, repository, cache)

        # Create test data
        document = Document(
            id="test_doc_2",
            title="Test Document 2",
            file_name="test2.pdf",
            file_path="test/test2.pdf",
            file_type="pdf",
            metadata={},
        )
        chunk = DocumentChunk(
            id="test_chunk_2",
            document_id="test_doc_2",
            content="Test content for caching.",
            chunk_index=0,
            embedding=[0.2] * 1536,
        )

        test_db.add(document)
        test_db.add(chunk)
        await test_db.commit()

        class MockState:
            def __init__(self) -> None:
                self.thread_id = "test_thread_456"
                self.query = "What is cached?"
                self.language = "pt-BR"
                self.agent_response = None

        state = MockState()

        # First call should generate embedding
        result1 = await agent.process(state)
        assert result1.agent_response is not None

        # Second call should use cache
        result2 = await agent.process(state)
        assert result2.agent_response is not None

