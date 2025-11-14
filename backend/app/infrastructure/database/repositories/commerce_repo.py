"""
Commerce repository (data access for commerce documents).

Overview
  Provides repository interface and PostgreSQL implementation for commerce
  document operations. Follows Repository pattern for abstraction and testability.

Design
  - **Repository Pattern**: Abstract interface with PostgreSQL implementation.
  - **Document Storage**: Stores commerce documents with JSONB for flexible schema.

Integration
  - Consumes: Database models, SQLAlchemy async session.
  - Returns: CommerceDocument models.
  - Used by: CommerceAgent for document storage and retrieval.
  - Observability: N/A (data access layer).

Usage
  >>> from app.infrastructure.database.repositories.commerce_repo import PostgreSQLCommerceRepository
  >>> repo = PostgreSQLCommerceRepository(session)
  >>> document = await repo.save_document(commerce_document)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.exceptions import DatabaseException
from app.infrastructure.database.models.commerce import CommerceDocument


class CommerceRepository(ABC):
    """Abstract repository interface for commerce document operations.

    Defines interface for commerce document data access operations.
    Concrete implementations provide database-specific logic.

    Methods:
        save_document: Save commerce document.
        get_document: Get document by ID.
        list_documents: List documents (optionally filtered by user).
    """

    @abstractmethod
    async def save_document(self, document: CommerceDocument) -> CommerceDocument:
        """Save commerce document.

        Saves document to database and returns saved document with ID.

        Args:
            document: CommerceDocument to save.

        Returns:
            Saved CommerceDocument with ID.
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[CommerceDocument]:
        """Get commerce document by ID.

        Args:
            document_id: Document ID (UUID string).

        Returns:
            CommerceDocument if found, None otherwise.
        """
        pass

    @abstractmethod
    async def list_documents(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CommerceDocument]:
        """List commerce documents.

        Lists documents, optionally filtered by user_id, ordered by created_at DESC.

        Args:
            user_id: User ID to filter by (optional).
            limit: Maximum number of documents to return.

        Returns:
            List of CommerceDocument objects.
        """
        pass


class PostgreSQLCommerceRepository(CommerceRepository):
    """PostgreSQL implementation of commerce repository.

    Provides PostgreSQL implementation for commerce document operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize PostgreSQL commerce repository.

        Args:
            session: Async database session.
        """
        self._session = session

    async def save_document(self, document: CommerceDocument) -> CommerceDocument:
        """Save commerce document to database.

        Saves document and returns saved document with ID.

        Args:
            document: CommerceDocument to save.

        Returns:
            Saved CommerceDocument with ID.

        Raises:
            DatabaseException: If save operation fails.
        """
        try:
            self._session.add(document)
            await self._session.flush()
            await self._session.refresh(document)
            return document
        except Exception as e:
            await self._session.rollback()
            raise DatabaseException(
                message=f"Failed to save commerce document: {str(e)}",
                details={"error": str(e)},
            ) from e

    async def get_document(self, document_id: str) -> Optional[CommerceDocument]:
        """Get commerce document by ID.

        Args:
            document_id: Document ID (UUID string).

        Returns:
            CommerceDocument if found, None otherwise.

        Raises:
            DatabaseException: If query fails.
        """
        try:
            doc_uuid = UUID(document_id)
            query = select(CommerceDocument).where(CommerceDocument.id == doc_uuid)
            result = await self._session.execute(query)
            document = result.scalar_one_or_none()
            return document
        except ValueError:
            # Invalid UUID format
            return None
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to retrieve commerce document: {str(e)}",
                details={"error": str(e), "document_id": document_id},
            ) from e

    async def list_documents(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CommerceDocument]:
        """List commerce documents.

        Lists documents ordered by created_at DESC, optionally filtered by user_id.

        Args:
            user_id: User ID to filter by (optional).
            limit: Maximum number of documents to return.

        Returns:
            List of CommerceDocument objects.

        Raises:
            DatabaseException: If query fails.
        """
        try:
            query = select(CommerceDocument).order_by(CommerceDocument.created_at.desc())

            if user_id:
                user_uuid = UUID(user_id)
                query = query.where(CommerceDocument.user_id == user_uuid)

            query = query.limit(limit)

            result = await self._session.execute(query)
            documents = result.scalars().all()
            return list(documents)
        except ValueError:
            # Invalid UUID format
            return []
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to list commerce documents: {str(e)}",
                details={"error": str(e), "user_id": user_id},
            ) from e

