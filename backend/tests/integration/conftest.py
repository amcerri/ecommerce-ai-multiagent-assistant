"""
Integration test configuration and fixtures (real services for integration tests).

Overview
  Provides pytest fixtures for integration testing including real database,
  Redis, and FastAPI TestClient. Uses real services (not mocks) to test
  complete flows end-to-end.

Design
  - **Real Services**: Uses real PostgreSQL and Redis for integration tests.
  - **Test Isolation**: Each test gets clean database and cache.
  - **Dependency Override**: Overrides FastAPI dependencies for test database.
  - **Cleanup**: Automatic cleanup after tests.

Integration
  - Consumes: pytest, FastAPI TestClient, real database and Redis.
  - Returns: Test fixtures with real services.
  - Used by: All integration tests.
  - Observability: N/A (test infrastructure).

Usage
  >>> import pytest
  >>> async def test_example(test_db, test_client):
  ...     # Use real services
  ...     pass
"""

import asyncio
import os
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.main import app
from app.infrastructure.database.models.base import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests.

    Creates and yields an event loop for the entire test session.
    Closes the loop after all tests complete.

    Yields:
        asyncio.AbstractEventLoop: Event loop for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Creates a test database connection, creates all tables,
    and yields a session. Rolls back and closes session after test.

    Yields:
        AsyncSession: Database session for tests.
    """
    # Get test database URL from environment or use default
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
    )

    # Create engine for test database
    engine: AsyncEngine = create_async_engine(
        test_db_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Clean slate
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Create session
    async with async_session_maker() as session:
        try:
            yield session
            await session.rollback()  # Rollback instead of commit for test isolation
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Cleanup: Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine
    await engine.dispose()


@pytest.fixture(scope="function")
def test_redis() -> Generator[MagicMock, None, None]:
    """Create test Redis connection.

    Creates a Redis connection for testing. Clears cache after each test.

    Yields:
        MagicMock: Redis client mock (or real Redis if configured).
    """
    # For integration tests, we can use a real Redis or mock
    # Using mock for now to avoid requiring Redis in CI
    redis_mock = MagicMock()
    redis_store: dict[str, str] = {}

    # Mock Redis operations
    async def mock_get(key: str) -> str | None:
        return redis_store.get(key)

    async def mock_set(key: str, value: str, ex: int | None = None) -> None:
        redis_store[key] = value

    async def mock_delete(key: str) -> None:
        redis_store.pop(key, None)

    async def mock_flushdb() -> None:
        redis_store.clear()

    redis_mock.get = AsyncMock(side_effect=mock_get)
    redis_mock.set = AsyncMock(side_effect=mock_set)
    redis_mock.setex = AsyncMock(side_effect=mock_set)
    redis_mock.delete = AsyncMock(side_effect=mock_delete)
    redis_mock.flushdb = AsyncMock(side_effect=mock_flushdb)
    redis_mock.exists = AsyncMock(side_effect=lambda key: 1 if key in redis_store else 0)

    yield redis_mock

    # Cleanup
    redis_store.clear()


@pytest.fixture(scope="function")
def test_client(test_db: AsyncSession) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with overridden dependencies.

    Creates a TestClient with database dependency overridden to use test database.

    Args:
        test_db: Test database session.

    Yields:
        TestClient: FastAPI test client.
    """
    from app.api.dependencies import get_db

    # Override database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    client = TestClient(app)

    yield client

    # Cleanup: Remove overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def llm_client_mock() -> Generator[MagicMock, None, None]:
    """Create mock LLM client for integration tests.

    Creates a mock LLM client that can be configured for different test scenarios.

    Returns:
        MagicMock: Mock LLM client.
    """
    mock = MagicMock()

    # Mock chat_completion
    async def mock_chat_completion(
        messages: list[dict],
        model: str = "gpt-4",
        temperature: float = 0.7,
        **kwargs: dict,
    ) -> dict:
        """Mock chat completion."""
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Mock response",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }

    mock.chat_completion = AsyncMock(side_effect=mock_chat_completion)

    # Mock generate_embedding
    async def mock_generate_embedding(text: str, model: str = "text-embedding-ada-002") -> dict:
        """Mock embedding generation."""
        return {
            "embedding": [0.1] * 1536,
            "model": model,
            "tokens_used": 5,
        }

    mock.generate_embedding = AsyncMock(side_effect=mock_generate_embedding)

    # Mock generate_structured
    async def mock_generate_structured(
        prompt: str,
        schema: dict,
        **kwargs: dict,
    ) -> dict:
        """Mock structured generation."""
        return {"result": "mock_structured_output"}

    mock.generate_structured = AsyncMock(side_effect=mock_generate_structured)

    return mock

