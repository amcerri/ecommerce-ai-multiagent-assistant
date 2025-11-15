"""
Integration tests for Commerce Agent.

Tests complete Commerce Agent pipeline with real database and dependencies.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.commerce.agent import CommerceAgent
from app.infrastructure.database.repositories.commerce_repo import (
    PostgreSQLCommerceRepository,
)
from app.infrastructure.storage.local_storage import LocalStorage


class TestCommerceAgentIntegration:
    """Integration tests for Commerce Agent."""

    @pytest.fixture
    def temp_storage(self) -> Path:
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_commerce_agent_pipeline(
        self,
        test_db: AsyncSession,
        llm_client_mock: Any,
        temp_storage: Path,
    ) -> None:
        """Test complete Commerce Agent pipeline."""
        # Create storage with temp directory
        storage = LocalStorage()
        storage.base_path = temp_storage

        # Create repository with real database
        repository = PostgreSQLCommerceRepository(test_db)

        # Create agent
        agent = CommerceAgent(llm_client_mock, storage, repository)

        # Create test PDF file
        test_file_path = temp_storage / "test_document.pdf"
        test_file_path.write_bytes(b"PDF content for testing")

        # Create graph state
        class MockState:
            def __init__(self) -> None:
                self.thread_id = "test_thread_commerce"
                self.query = "Process this document"
                self.language = "pt-BR"
                self.file_path = str(test_file_path.relative_to(temp_storage))
                self.file_type = "pdf"
                self.agent_response = None

        state = MockState()

        # Process with agent
        result = await agent.process(state)

        # Verify result
        assert hasattr(result, "agent_response")
        assert result.agent_response is not None
        assert result.agent_response.agent == "commerce"

    @pytest.mark.asyncio
    async def test_commerce_agent_missing_file(
        self,
        test_db: AsyncSession,
        llm_client_mock: Any,
        temp_storage: Path,
    ) -> None:
        """Test Commerce Agent with missing file."""
        storage = LocalStorage()
        storage.base_path = temp_storage
        repository = PostgreSQLCommerceRepository(test_db)

        agent = CommerceAgent(llm_client_mock, storage, repository)

        class MockState:
            def __init__(self) -> None:
                self.thread_id = "test_thread_missing"
                self.query = "Process document"
                self.language = "pt-BR"
                self.file_path = "nonexistent.pdf"
                self.file_type = "pdf"
                self.agent_response = None

        state = MockState()

        # Should handle missing file gracefully
        result = await agent.process(state)
        assert hasattr(result, "agent_response")

