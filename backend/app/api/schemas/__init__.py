"""
API schemas module (Pydantic models for request/response validation).

Overview
  Provides Pydantic models for API request and response validation.
  Schemas will be fully implemented in Batch 21. For now, stubs are provided
  to allow Batch 19 routes to compile.

Design
  - **Pydantic Models**: Type-safe request/response models.
  - **Validation**: Automatic validation of request data.
  - **Serialization**: Automatic serialization of response data.

Integration
  - Consumes: Contracts (Answer, RouterDecision), database models.
  - Returns: Validated request/response models.
  - Used by: API route handlers.
  - Observability: N/A (validation only).

Usage
  >>> from app.api.schemas.chat import ChatRequest, ChatResponse
  >>> request = ChatRequest(query="Hello", thread_id="...")
  >>> response = ChatResponse(message_id="...", thread_id="...", response=answer)
"""

# Chat schemas (stubs for Batch 19, will be fully implemented in Batch 21)
from app.api.schemas.chat import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ChatHistoryResponse",
]

