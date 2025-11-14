"""
Document API schemas (request/response models for document endpoints).

Overview
  Provides Pydantic models for document API endpoints. Defines request and response
  structures for document upload, processing, analysis, and listing. Only commerce
  documents can be uploaded by users (knowledge and analytics are processed via
  administrative scripts).

Design
  - **Request Models**: DocumentUploadRequest for document uploads (type validation).
  - **Response Models**: DocumentResponse for document information, DocumentListResponse for lists.
  - **Validation**: Automatic validation with Pydantic (status enum, confidence range, etc.).
  - **Serialization**: Automatic JSON serialization for API responses.

Integration
  - Consumes: Database models (CommerceDocument).
  - Returns: Validated request/response models.
  - Used by: Document API routes (Batch 20).
  - Observability: N/A (validation only).

Usage
  >>> from app.api.schemas.documents import DocumentResponse, DocumentListResponse
  >>> response = DocumentResponse(document_id="...", filename="...", status="processed")
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentUploadRequest(BaseModel):
    """Request model for document upload.

    Validates document type for uploads. Only commerce documents can be
    uploaded by users (knowledge and analytics are processed via administrative scripts).

    Attributes:
        type: Document type (must be "commerce" for user uploads).

    Validation:
        - type must be "commerce"
    """

    type: Literal["commerce"] = Field(
        default="commerce",
        description="Document type (must be 'commerce' for user uploads)",
    )


class DocumentResponse(BaseModel):
    """Response model for document information.

    Contains complete information about a processed document including
    extracted data, schema, confidence score, and processing metadata.

    Attributes:
        document_id: Unique document ID (UUID string).
        filename: Original filename.
        file_type: File type (pdf, docx, txt, png, jpg, etc.).
        status: Processing status ("pending", "processing", "processed", "error", "stored").
        extracted_data: Extracted data from document (JSONB, dynamic schema).
        schema_definition: Detected schema definition (JSONB).
        confidence_score: Extraction confidence score (0.0-1.0, optional).
        processing_metadata: Processing metadata (OCR, timing, errors, etc.).
        created_at: Document creation timestamp.
        processed_at: Document processing completion timestamp (optional).

    Validation:
        - status must be one of the allowed values
        - confidence_score must be between 0.0 and 1.0 if provided
    """

    document_id: str = Field(..., description="Unique document ID (UUID)")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx, txt, png, jpg, etc.)")
    status: Literal["pending", "processing", "processed", "error", "stored"] = Field(
        ...,
        description="Processing status",
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted data from document (JSONB, dynamic schema)",
    )
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="Detected schema definition (JSONB)",
        alias="schema",
    )
    confidence_score: Optional[float] = Field(
        None,
        description="Extraction confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    processing_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Processing metadata (OCR, timing, errors, etc.)",
    )
    created_at: datetime = Field(..., description="Document creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Document processing completion timestamp")

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, v: str) -> str:
        """Validate document_id is valid UUID format.

        Args:
            v: Document ID string.

        Returns:
            Validated document ID.

        Raises:
            ValueError: If not a valid UUID format.
        """
        import uuid

        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("document_id must be a valid UUID format")
        return v


class DocumentListResponse(BaseModel):
    """Response model for document listing.

    Contains paginated list of documents with total count and pagination parameters.

    Attributes:
        documents: List of documents (DocumentResponse).
        total: Total number of documents (before pagination).
        limit: Limit applied for pagination.
        offset: Offset applied for pagination.

    Validation:
        - total must be >= 0
        - limit must be > 0
        - offset must be >= 0
    """

    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents (before pagination)", ge=0)
    limit: int = Field(..., description="Limit applied for pagination", gt=0)
    offset: int = Field(..., description="Offset applied for pagination", ge=0)
