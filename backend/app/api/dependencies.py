"""
API dependencies (FastAPI dependency injection).

Overview
  Provides dependency injection functions for FastAPI routes. All dependencies
  use singletons or context managers for efficient resource management.

Design
  - **Dependency Injection**: Uses FastAPI Depends() for dependency injection.
  - **Singletons**: Uses singleton functions for services (LLM, cache, graph).
  - **Context Managers**: Uses context managers for database sessions.
  - **Async Support**: All dependencies support async operations.

Integration
  - Consumes: Infrastructure singletons (get_db_session, get_llm_client, etc.).
  - Returns: Service instances for route handlers.
  - Used by: All API route handlers.
  - Observability: N/A (dependency injection only).

Usage
  >>> from app.api.dependencies import get_db, get_llm
  >>> @router.get("/endpoint")
  >>> async def endpoint(db: AsyncSession = Depends(get_db)):
  ...     # Use db session
  """

from typing import Annotated, Any, AsyncGenerator, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.build import build_graph
from app.infrastructure.cache.cache_manager import CacheManager, get_cache_manager
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.llm import get_llm_client
from app.infrastructure.llm.client import LLMClient
from app.services.language.detector import LanguageDetector


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Provides async database session as FastAPI dependency.
    Session is automatically closed after request.

    Yields:
        AsyncSession: Database session.

    Yields:
        AsyncSession: Database session context manager.
    """
    async with get_db_session() as session:
        yield session


def get_llm() -> LLMClient:
    """Get LLM client dependency.

    Provides LLM client instance as FastAPI dependency.
    Uses singleton for efficiency.

    Returns:
        LLMClient: LLM client instance.
    """
    return get_llm_client()


def get_cache() -> Optional[CacheManager]:
    """Get cache manager dependency.

    Provides cache manager instance as FastAPI dependency.
    Uses singleton for efficiency. Returns None if cache unavailable.

    Returns:
        CacheManager: Cache manager instance, or None if unavailable.
    """
    return get_cache_manager()


def get_assistant() -> Any:  # type: ignore
    """Get LangGraph assistant dependency.

    Provides compiled LangGraph graph as FastAPI dependency.
    Uses build_graph() to create graph instance.

    Returns:
        Compiled LangGraph StateGraph.
    """
    from app.graph.build import build_graph

    return build_graph(require_sql_approval=True)


def get_language_detector() -> LanguageDetector:
    """Get language detector dependency.

    Provides language detector instance as FastAPI dependency.
    Creates new instance (stateless).

    Returns:
        LanguageDetector: Language detector instance.
    """
    return LanguageDetector()


# Type aliases for convenience
DBDep = Annotated[AsyncSession, Depends(get_db)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]
CacheDep = Annotated[Optional[CacheManager], Depends(get_cache)]
AssistantDep = Annotated[Any, Depends(get_assistant)]  # type: ignore
LanguageDetectorDep = Annotated[LanguageDetector, Depends(get_language_detector)]

