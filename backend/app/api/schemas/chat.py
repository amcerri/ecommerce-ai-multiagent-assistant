"""
Chat API schemas (request/response models for chat endpoints).

Overview
  Provides Pydantic models for chat API endpoints. These are stub implementations
  that will be fully implemented in Batch 21. For now, they provide basic structure
  to allow Batch 19 routes to compile and function.

Design
  - **Request Models**: ChatRequest for incoming messages.
  - **Response Models**: ChatResponse for message responses, ChatHistoryResponse for history.
  - **Validation**: Basic validation with Pydantic.
  - **Serialization**: Automatic JSON serialization.

Integration
  - Consumes: Contracts (Answer), database models (Message).
  - Returns: Validated request/response models.
  - Used by: Chat API routes.
  - Observability: N/A (validation only).

Usage
  >>> from app.api.schemas.chat import ChatRequest, ChatResponse
  >>> request = ChatRequest(query="Hello", thread_id="...")
  >>> response = ChatResponse(message_id="...", thread_id="...", response=answer)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for sending chat messages.

    Attributes:
        query: User query text.
        thread_id: Conversation thread ID (optional, generated if not provided).
        attachment: Optional file attachment (path or URL).
    """

    query: str = Field(..., description="User query text", min_length=1)
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")
    attachment: Optional[str] = Field(None, description="Optional file attachment")


class ChatResponse(BaseModel):
    """Response model for chat messages.

    Attributes:
        message_id: Unique message ID.
        thread_id: Conversation thread ID.
        response: Agent response (Answer contract).
        language: Detected language.
        metadata: Additional metadata (citations, SQL, performance, etc.).
    """

    message_id: str = Field(..., description="Unique message ID")
    thread_id: str = Field(..., description="Conversation thread ID")
    response: Any = Field(..., description="Agent response (Answer contract)")  # type: ignore
    language: str = Field(..., description="Detected language")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatHistoryResponse(BaseModel):
    """Response model for conversation history.

    Attributes:
        thread_id: Conversation thread ID.
        messages: List of messages in the conversation.
        total: Total number of messages.
    """

    thread_id: str = Field(..., description="Conversation thread ID")
    messages: List[Dict[str, Any]] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages")

