"""
Database connection manager (async PostgreSQL connection pooling).

Overview
  Manages async SQLAlchemy engine and session factory with connection pooling
  for efficient database access across the application. Provides context manager
  for automatic session management with commit/rollback handling.

Design
  - **Async Engine**: Uses asyncpg driver for non-blocking database operations.
  - **Connection Pooling**: Configurable pool size and overflow for scalability.
  - **Session Management**: Context manager pattern for automatic commit/rollback.
  - **Dependencies**: Requires app.config.settings for database URL and app.config.constants for pool settings.

Integration
  - Consumes: Database URL from settings, pool constants from app.config.constants.
  - Returns: Async session context manager and engine.
  - Used by: All repository classes and database operations.
  - Observability: Connection pool metrics, query timing.

Usage
  >>> from app.infrastructure.database.connection import get_db_session
  >>> async with get_db_session() as session:
  ...     result = await session.execute(select(User))
  ...     users = result.scalars().all()
"""

import contextlib
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.constants import (
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
)
from app.config.settings import get_settings

# Lazy initialization - engine created on first access
_engine: AsyncEngine | None = None
_AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    """Get or create async database engine.

    Creates engine on first call using settings and constants.
    Subsequent calls return the same engine instance.

    Returns:
        AsyncEngine: Async database engine.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        # Convert postgresql:// to postgresql+asyncpg:// for async driver
        database_url = settings.database_url.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )
        # Create async engine with connection pooling
        _engine = create_async_engine(
            database_url,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_timeout=DB_POOL_TIMEOUT,
            pool_recycle=DB_POOL_RECYCLE,
            echo=settings.debug,
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create async session factory.

    Creates session factory on first call using engine.
    Subsequent calls return the same factory instance.

    Returns:
        async_sessionmaker: Async session factory.
    """
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        engine = _get_engine()
        # Create async session factory
        _AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


@contextlib.asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with automatic commit/rollback.

    Context manager that provides an async database session with automatic
    transaction management. Commits on success, rolls back on exception,
    and always closes the session.

    Yields:
        AsyncSession: Database session for executing queries.

    Example:
        >>> async with get_db_session() as session:
        ...     result = await session.execute(select(User))
        ...     users = result.scalars().all()
    """
    AsyncSessionLocal = _get_session_factory()
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_db_engine() -> AsyncEngine:
    """Get async database engine.

    Returns the global async database engine. Useful for operations that
    need direct engine access (migrations, initialization, etc.).

    Returns:
        AsyncEngine: Global async database engine.
    """
    return _get_engine()


async def init_db() -> None:
    """Initialize database by creating all tables.

    Creates all database tables defined in models by executing
    Base.metadata.create_all() within an async transaction.

    Note:
        This should be called during application startup or setup.
        In production, use Alembic migrations instead.
    """
    from app.infrastructure.database.models.base import Base

    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

