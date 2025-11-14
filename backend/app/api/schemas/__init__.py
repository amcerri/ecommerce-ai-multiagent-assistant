"""
API schemas module (Pydantic models for request/response validation).

Overview
  Provides Pydantic models for API request and response validation. All schemas
  use Pydantic for automatic validation, type safety, and JSON serialization.
  Schemas are organized by domain (chat, documents, health).

Design
  - **Pydantic Models**: Type-safe request/response models with automatic validation.
  - **Validation**: Automatic validation of request data (UUID, ranges, enums, etc.).
  - **Serialization**: Automatic JSON serialization of response data.
  - **Type Safety**: Full type hints with Literal types for restricted values.

Integration
  - Consumes: Contracts (Answer), database models (Message, Conversation, CommerceDocument).
  - Returns: Validated request/response models.
  - Used by: API route handlers (Batches 19, 20).
  - Observability: N/A (validation only).

Usage
  >>> from app.api.schemas.chat import ChatRequest, ChatResponse
  >>> request = ChatRequest(query="Hello", thread_id="...")
  >>> response = ChatResponse(message_id="...", thread_id="...", response=answer)
"""

# Chat schemas
from app.api.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)

# Document schemas
from app.api.schemas.documents import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadRequest,
)

# Health schemas
from app.api.schemas.health import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)

__all__ = [
    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    "ChatHistoryResponse",
    # Document schemas
    "DocumentUploadRequest",
    "DocumentResponse",
    "DocumentListResponse",
    # Health schemas
    "HealthResponse",
    "ReadinessResponse",
    "LivenessResponse",
]

