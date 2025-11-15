"""
Test configuration and fixtures (shared fixtures for all tests).

Overview
  Provides pytest fixtures for testing including database sessions, mocks
  for external dependencies (LLM, cache, storage), and test utilities.

Design
  - **Database**: Uses SQLite in-memory database for fast tests.
  - **Mocks**: Provides mocks for all external dependencies.
  - **Fixtures**: Reusable fixtures for common test scenarios.
  - **Cleanup**: Automatic cleanup after tests.

Integration
  - Consumes: pytest, SQLAlchemy, unittest.mock.
  - Returns: Test fixtures and mocks.
  - Used by: All unit tests.
  - Observability: N/A (test infrastructure).

Usage
  >>> import pytest
  >>> async def test_example(db_session, llm_client_mock):
  ...     # Use fixtures
  ...     pass
"""

import asyncio
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

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


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests.

    Creates an in-memory SQLite database, creates all tables,
    and yields a session. Rolls back and closes session after test.

    Yields:
        AsyncSession: Database session for tests.
    """
    # Create in-memory SQLite database
    engine: AsyncEngine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
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
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Cleanup
    await engine.dispose()


@pytest.fixture
def llm_client_mock() -> MagicMock:
    """Create mock LLM client.

    Creates a mock LLM client with common methods (chat_completion,
    generate_embedding, etc.) that return configurable default values.

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
    async def mock_generate_embedding(text: str, model: str = "text-embedding-ada-002") -> list[float]:
        """Mock embedding generation."""
        # Return a mock embedding vector (1536 dimensions for ada-002)
        return [0.1] * 1536

    mock.generate_embedding = AsyncMock(side_effect=mock_generate_embedding)

    return mock


@pytest.fixture
def cache_mock() -> MagicMock:
    """Create mock cache manager.

    Creates a mock cache manager with methods (get, set, delete)
    that simulate in-memory cache behavior.

    Returns:
        MagicMock: Mock cache manager.
    """
    mock = MagicMock()
    cache_store: dict[str, Any] = {}

    # Mock get
    async def mock_get(key: str, namespace: str = "default") -> Any:
        """Mock cache get."""
        full_key = f"{namespace}:{key}"
        return cache_store.get(full_key)

    mock.get = AsyncMock(side_effect=mock_get)

    # Mock set
    async def mock_set(key: str, value: Any, namespace: str = "default", ttl: int | None = None) -> None:
        """Mock cache set."""
        full_key = f"{namespace}:{key}"
        cache_store[full_key] = value

    mock.set = AsyncMock(side_effect=mock_set)

    # Mock delete
    async def mock_delete(key: str, namespace: str = "default") -> None:
        """Mock cache delete."""
        full_key = f"{namespace}:{key}"
        cache_store.pop(full_key, None)

    mock.delete = AsyncMock(side_effect=mock_delete)

    # Mock clear
    async def mock_clear(namespace: str | None = None) -> None:
        """Mock cache clear."""
        if namespace:
            keys_to_delete = [k for k in cache_store.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_delete:
                del cache_store[key]
        else:
            cache_store.clear()

    mock.clear = AsyncMock(side_effect=mock_clear)

    return mock


@pytest.fixture
def storage_mock() -> MagicMock:
    """Create mock storage.

    Creates a mock storage with methods (save, get, delete)
    that simulate in-memory storage behavior.

    Returns:
        MagicMock: Mock storage.
    """
    mock = MagicMock()
    storage_store: dict[str, bytes] = {}

    # Mock save
    async def mock_save(file_path: str, content: bytes) -> str:
        """Mock storage save."""
        storage_store[file_path] = content
        return file_path

    mock.save = AsyncMock(side_effect=mock_save)

    # Mock get
    async def mock_get(file_path: str) -> bytes | None:
        """Mock storage get."""
        return storage_store.get(file_path)

    mock.get = AsyncMock(side_effect=mock_get)

    # Mock delete
    async def mock_delete(file_path: str) -> None:
        """Mock storage delete."""
        storage_store.pop(file_path, None)

    mock.delete = AsyncMock(side_effect=mock_delete)

    # Mock exists
    async def mock_exists(file_path: str) -> bool:
        """Mock storage exists."""
        return file_path in storage_store

    mock.exists = AsyncMock(side_effect=mock_exists)

    return mock


@pytest.fixture
def graph_state() -> dict:
    """Create sample graph state for tests.

    Creates a sample GraphState dictionary with required fields
    for testing agent processing.

    Returns:
        dict: Sample GraphState dictionary.
    """
    return {
        "thread_id": "test_thread_123",
        "user_id": "test_user_123",
        "query": "Test query",
        "language": "pt-BR",
        "conversation_history": [],
        "metadata": {},
        "interrupts": {},
    }

