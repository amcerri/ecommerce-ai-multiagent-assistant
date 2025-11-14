"""
Database repositories module (data access abstraction layer).

Overview
  Provides repository interfaces and implementations for data access.
  Follows Repository pattern for abstraction and testability.

Design
  - **Repository Pattern**: Abstract interfaces with concrete implementations.
  - **Abstraction**: Separates data access from business logic.
  - **Testability**: Easy to mock repositories for testing.

Integration
  - Consumes: Database models, SQLAlchemy sessions.
  - Returns: Domain models and data structures.
  - Used by: Agents and services for data access.
  - Observability: N/A (data access layer).

Usage
  >>> from app.infrastructure.database.repositories.knowledge_repo import PostgreSQLKnowledgeRepository
  >>> repo = PostgreSQLKnowledgeRepository(session)
  >>> chunks = await repo.get_chunks_by_embedding(embedding, top_k=10)
"""

from app.infrastructure.database.repositories.analytics_repo import (
    AnalyticsRepository,
    PostgreSQLAnalyticsRepository,
)
from app.infrastructure.database.repositories.knowledge_repo import (
    KnowledgeRepository,
    PostgreSQLKnowledgeRepository,
)

__all__ = [
    "KnowledgeRepository",
    "PostgreSQLKnowledgeRepository",
    "AnalyticsRepository",
    "PostgreSQLAnalyticsRepository",
]

