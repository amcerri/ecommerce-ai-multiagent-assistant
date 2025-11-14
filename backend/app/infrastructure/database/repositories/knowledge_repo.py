"""
Knowledge repository (data access for knowledge base).

Overview
  Provides repository interface and PostgreSQL implementation for knowledge base
  operations. Uses pgvector for vector similarity search. Follows Repository pattern
  for abstraction and testability.

Design
  - **Repository Pattern**: Abstract interface with PostgreSQL implementation.
  - **Vector Search**: Uses pgvector for cosine similarity search.
  - **Eager Loading**: Loads Document relationship with chunks.

Integration
  - Consumes: Database models, SQLAlchemy async session, pgvector.
  - Returns: DocumentChunk models with Document relationship loaded.
  - Used by: KnowledgeRetriever for vector search.
  - Observability: N/A (data access layer).

Usage
  >>> from app.infrastructure.database.repositories.knowledge_repo import PostgreSQLKnowledgeRepository
  >>> repo = PostgreSQLKnowledgeRepository(session)
  >>> chunks = await repo.get_chunks_by_embedding(embedding, top_k=10)
"""

from abc import ABC, abstractmethod
from typing import List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.exceptions import DatabaseException
from app.infrastructure.database.models.knowledge import DocumentChunk


class KnowledgeRepository(ABC):
    """Abstract repository interface for knowledge base operations.

    Defines interface for knowledge base data access operations.
    Concrete implementations provide database-specific logic.

    Methods:
        get_chunks_by_embedding: Search chunks by vector similarity.
    """

    @abstractmethod
    async def get_chunks_by_embedding(
        self,
        embedding: List[float],
        top_k: int,
    ) -> List[DocumentChunk]:
        """Get chunks by embedding similarity.

        Searches for document chunks using vector similarity search.
        Returns top_k most similar chunks ordered by similarity.

        Args:
            embedding: Query embedding vector.
            top_k: Number of chunks to return.

        Returns:
            List of DocumentChunk objects ordered by similarity.
        """
        pass


class PostgreSQLKnowledgeRepository(KnowledgeRepository):
    """PostgreSQL implementation of knowledge repository.

    Provides PostgreSQL/pgvector implementation for knowledge base operations.
    Uses cosine distance for similarity search.

    Attributes:
        _session: Async database session.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize PostgreSQL knowledge repository.

        Args:
            session: Async database session.
        """
        self._session = session

    async def get_chunks_by_embedding(
        self,
        embedding: List[float],
        top_k: int,
    ) -> List[DocumentChunk]:
        """Get chunks by embedding similarity using pgvector.

        Searches for chunks using cosine distance with pgvector.
        Returns top_k most similar chunks with Document relationship loaded.

        Args:
            embedding: Query embedding vector.
            top_k: Number of chunks to return.

        Returns:
            List of DocumentChunk objects ordered by similarity (most similar first).

        Raises:
            DatabaseException: If database query fails.
        """
        try:
            # Build query with cosine distance using pgvector
            # pgvector uses <-> operator for cosine distance (1 - cosine similarity)
            # Lower distance = higher similarity
            # Convert embedding list to PostgreSQL array format
            embedding_str = "[" + ",".join(map(str, embedding)) + "]"
            
            # Use raw SQL for pgvector operator
            # <-> is cosine distance operator in pgvector
            # We need to use text() for the order_by clause
            query = (
                select(DocumentChunk)
                .where(DocumentChunk.embedding.isnot(None))
                .order_by(
                    text(f"document_chunks.embedding <-> '{embedding_str}'::vector")
                )
                .limit(top_k)
                .options(selectinload(DocumentChunk.document))
            )

            # Execute query
            result = await self._session.execute(query)
            chunks = result.scalars().all()

            return list(chunks)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve chunks by embedding: {str(e)}",
                details={"error": str(e), "top_k": top_k},
            ) from e

