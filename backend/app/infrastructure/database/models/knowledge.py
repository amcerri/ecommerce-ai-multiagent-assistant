"""
Knowledge base models (documents and chunks with vector embeddings).

Overview
  Defines database models for knowledge base including documents and document
  chunks with vector embeddings for semantic search. Uses pgvector for storing
  and querying embeddings.

Design
  - **Vector Embeddings**: Uses pgvector Vector type for storing embeddings.
  - **Embedding Dimension**: Uses EMBEDDING_DIMENSION from constants (1536 for OpenAI).
  - **Cascade Delete**: Deleting a document automatically deletes its chunks.
  - **Relationships**: Bidirectional relationships with back_populates.

Integration
  - Consumes: app.config.constants.EMBEDDING_DIMENSION, pgvector.
  - Returns: Document and DocumentChunk model classes.
  - Used by: Knowledge agent, document ingestion, vector search.
  - Observability: N/A (models only).

Usage
  >>> from app.infrastructure.database.models.knowledge import Document, DocumentChunk
  >>> document = Document(title="Test", file_name="test.pdf", ...)
  >>> chunk = DocumentChunk(document_id=document.id, content="...", ...)
"""

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.config.constants import EMBEDDING_DIMENSION
from app.infrastructure.database.models.base import BaseModel
from pgvector.sqlalchemy import Vector


class Document(BaseModel):
    """Model for knowledge base documents.

    Represents a document (PDF, DOCX, etc.) in the knowledge base.
    Documents are split into chunks for vector search and retrieval.

    Attributes:
        title: Document title.
        file_name: Original filename.
        file_path: Storage path for the file.
        file_type: File type (e.g., "pdf", "docx").
        page_count: Number of pages (optional).
        meta: Additional metadata as JSON (optional).
        chunks: Relationship to document chunks (one-to-many).

    Note:
        Deleting a document cascades to delete all its chunks.
    """

    __tablename__ = "documents"

    title = Column(Text, nullable=False)
    file_name = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(Text, nullable=False)
    page_count = Column(Integer, nullable=True)
    meta = Column(JSON, nullable=True)

    # Relationships
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(BaseModel):
    """Model for document chunks with vector embeddings.

    Represents a chunk of a document with its vector embedding for
    semantic search. Chunks are created by splitting documents and
    embeddings are generated using LLM embedding models.

    Attributes:
        document_id: Foreign key to parent document.
        chunk_index: Index of chunk within document.
        content: Text content of the chunk.
        embedding: Vector embedding (pgvector, dimension from constants).
        page_number: Page number where chunk appears (optional).
        meta: Additional metadata as JSON (optional).
        document: Relationship to parent document (many-to-one).

    Note:
        Embedding dimension is 1536 for OpenAI text-embedding-3-small.
    """

    __tablename__ = "document_chunks"

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)
    page_number = Column(Integer, nullable=True)
    meta = Column(JSON, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")

