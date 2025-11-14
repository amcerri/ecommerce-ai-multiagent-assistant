"""
Commerce models (commercial documents with dynamic schema).

Overview
  Defines database models for commercial documents (orders, invoices, etc.)
  with dynamic schema stored as JSONB. Documents are processed by OCR/LLM
  and extracted data is stored flexibly based on detected document type.

Design
  - **Dynamic Schema**: Uses JSONB for extracted_data and schema_definition.
  - **Optional User**: user_id is optional to allow anonymous document processing.
  - **Processing Metadata**: Stores OCR confidence, processing time, etc.
  - **Relationships**: Optional relationship to User.

Integration
  - Consumes: app.infrastructure.database.models.conversation.User.
  - Returns: CommerceDocument model class.
  - Used by: Commerce agent, document processor, OCR/LLM extraction.
  - Observability: N/A (models only).

Usage
  >>> from app.infrastructure.database.models.commerce import CommerceDocument
  >>> doc = CommerceDocument(
  ...     file_name="invoice.pdf",
  ...     extracted_data={"total": 100.0, "items": [...]},
  ...     schema_definition={"fields": [...]}
  ... )
"""

from sqlalchemy import Column, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel


class CommerceDocument(BaseModel):
    """Model for commercial documents with dynamic schema.

    Represents a processed commercial document (order, invoice, etc.)
    with extracted data stored in JSONB format. Schema is detected
    dynamically by LLM based on document type.

    Attributes:
        user_id: Foreign key to user (optional, allows anonymous documents).
        file_name: Original filename.
        file_type: File type (e.g., "pdf", "docx", "png").
        file_path: Storage path for the file.
        extracted_data: Extracted data as JSON (dynamic schema).
        schema_definition: Detected schema definition as JSON.
        processing_metadata: Processing metadata (OCR, confidence, timing) as JSON (optional).
        confidence_score: Extraction confidence score (0.0-1.0, optional).
        user: Relationship to user (many-to-one, optional).

    Note:
        extracted_data and schema_definition use JSONB for flexible storage.
        user_id is optional to support anonymous document processing.
    """

    __tablename__ = "commerce_documents"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    file_name = Column(Text, nullable=False)
    file_type = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    extracted_data = Column(JSON, nullable=False)
    schema_definition = Column(JSON, nullable=False)
    processing_metadata = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Relationships
    user = relationship("User", back_populates="commerce_documents")

