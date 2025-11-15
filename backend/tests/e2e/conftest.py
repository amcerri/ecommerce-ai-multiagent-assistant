"""
E2E test configuration and fixtures (complete environment for end-to-end tests).

Overview
  Provides pytest fixtures for end-to-end testing with complete environment
  including real database, cache, and API server. Tests complete user journeys
  from API requests to database persistence.

Design
  - **Complete Environment**: Real services (database, cache, API).
  - **Test Isolation**: Each test gets clean environment.
  - **HTTP Client**: Real HTTP client (not TestClient) for E2E testing.
  - **Cleanup**: Automatic cleanup after tests.

Integration
  - Consumes: Real database, cache, API server.
  - Returns: Test fixtures with complete environment.
  - Used by: All E2E tests.
  - Observability: N/A (test infrastructure).

Usage
  >>> import pytest
  >>> async def test_example(e2e_client, e2e_environment):
  ...     # Use complete environment
  ...     pass
"""

import asyncio
import os
from typing import Any, AsyncGenerator, Dict, Generator

import httpx
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


@pytest.fixture(scope="function")
async def e2e_db() -> AsyncGenerator[AsyncSession, None]:
    """Create E2E test database session.

    Creates a test database connection, creates all tables,
    and yields a session. Rolls back and closes session after test.

    Yields:
        AsyncSession: Database session for E2E tests.
    """
    # Get test database URL from environment or use default
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_e2e_db",
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
            await session.rollback()  # Rollback for test isolation
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
def e2e_environment(e2e_db: AsyncSession) -> Dict[str, Any]:
    """Create complete E2E environment.

    Creates and returns configuration for complete E2E test environment
    including database, cache, and API configuration.

    Args:
        e2e_db: E2E database session.

    Returns:
        Dictionary with environment configuration.
    """
    # Get API base URL from environment or use default
    api_base_url = os.getenv("E2E_API_BASE_URL", "http://localhost:8000")

    return {
        "database": e2e_db,
        "api_base_url": api_base_url,
        "headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    }


@pytest.fixture(scope="function")
async def e2e_client(e2e_environment: Dict[str, Any]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create HTTP client for E2E tests.

    Creates an async HTTP client that connects to the real API server.
    Uses real HTTP requests (not TestClient) for true end-to-end testing.

    Args:
        e2e_environment: E2E environment configuration.

    Yields:
        httpx.AsyncClient: Async HTTP client for E2E tests.
    """
    base_url = e2e_environment["api_base_url"]
    headers = e2e_environment["headers"]

    client = httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        timeout=30.0,  # Longer timeout for E2E tests
    )

    yield client

    # Cleanup: Close client
    asyncio.run(client.aclose())

