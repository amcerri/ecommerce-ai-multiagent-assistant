"""
Document API schemas (request/response models for document endpoints).

Overview
  Provides Pydantic models for document API endpoints. These are stub implementations
  that will be fully implemented in Batch 21. For now, they provide basic structure
  to allow Batch 20 routes to compile and function.

Design
  - **Request Models**: DocumentUploadRequest for file uploads.
  - **Response Models**: DocumentResponse for document information, DocumentListResponse for lists.
  - **Validation**: Basic validation with Pydantic.
  - **Serialization**: Automatic JSON serialization.

Integration
  - Consumes: Database models (CommerceDocument).
  - Returns: Validated request/response models.
  - Used by: Document API routes.
  - Observability: N/A (validation only).

Usage
  >>> from app.api.schemas.documents import DocumentResponse, DocumentListResponse
  >>> response = DocumentResponse(document_id="...", filename="...", status="processed")
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    """Request model for document upload.

    Attributes:
        type: Document type (must be "commerce" for user uploads).
    """

    type: str = Field(default="commerce", description="Document type (must be 'commerce')")


class DocumentResponse(BaseModel):
    """Response model for document information.

    Attributes:
        document_id: Unique document ID (UUID).
        filename: Original filename.
        file_type: File type (pdf, docx, txt, png, jpg, etc.).
        status: Processing status (pending, processed, error, stored).
        extracted_data: Extracted data from document (JSON).
        schema: Detected schema (JSON).
        confidence_score: Confidence score (0.0-1.0).
        processing_metadata: Processing metadata (JSON).
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    file_type: Optional[str] = Field(None, description="File type")
    status: str = Field(..., description="Processing status")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Extracted data")
    schema_definition: Optional[Dict[str, Any]] = Field(None, description="Detected schema", alias="schema")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class DocumentListResponse(BaseModel):
    """Response model for document listing.

    Attributes:
        documents: List of documents.
        total: Total number of documents.
        limit: Limit used for pagination.
        offset: Offset used for pagination.
    """

    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination")

