"""
Chat API schemas (request/response models for chat endpoints).

Overview
  Provides Pydantic models for chat API endpoints. Defines request and response
  structures for message sending, streaming, and conversation history management.
  Uses Answer contract for agent responses.

Design
  - **Request Models**: ChatRequest for incoming messages with optional attachments.
  - **Response Models**: ChatResponse for message responses, ChatHistoryResponse for history.
  - **Validation**: Automatic validation with Pydantic (UUID, non-empty strings, etc.).
  - **Serialization**: Automatic JSON serialization for API responses.

Integration
  - Consumes: Contracts (Answer), database models (Message, Conversation).
  - Returns: Validated request/response models.
  - Used by: Chat API routes (Batch 19).
  - Observability: N/A (validation only).

Usage
  >>> from app.api.schemas.chat import ChatRequest, ChatResponse
  >>> request = ChatRequest(query="Hello", thread_id="...")
  >>> response = ChatResponse(message_id="...", thread_id="...", response=answer)
"""

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.contracts.answer import Answer


class ChatRequest(BaseModel):
    """Request model for sending chat messages.

    Validates incoming chat requests with query text, optional thread ID,
    and optional file attachment for commerce documents.

    Attributes:
        query: User query text (required, non-empty).
        thread_id: Conversation thread ID (optional, generates new if not provided).
        attachment: Optional file attachment for commerce documents.
            Structure: {"filename": str, "content": str, "mime_type": str}

    Validation:
        - query must be non-empty string
        - thread_id must be valid UUID format if provided
    """

    query: str = Field(..., description="User query text", min_length=1)
    thread_id: Optional[str] = Field(None, description="Conversation thread ID (UUID)")
    attachment: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional file attachment for commerce documents",
    )

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate thread_id is valid UUID format if provided.

        Args:
            v: Thread ID string or None.

        Returns:
            Validated thread ID or None.

        Raises:
            ValueError: If thread_id is not a valid UUID format.
        """
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("thread_id must be a valid UUID format")
        return v

    @field_validator("attachment")
    @classmethod
    def validate_attachment(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate attachment structure if provided.

        Args:
            v: Attachment dictionary or None.

        Returns:
            Validated attachment or None.

        Raises:
            ValueError: If attachment structure is invalid.
        """
        if v is not None:
            required_keys = {"filename", "content", "mime_type"}
            if not all(key in v for key in required_keys):
                raise ValueError(f"attachment must contain keys: {required_keys}")
        return v


class ChatResponse(BaseModel):
    """Response model for chat messages.

    Contains agent response with message ID, thread ID, Answer contract,
    detected language, and optional metadata (citations, SQL, performance).

    Attributes:
        message_id: Unique message ID (UUID string).
        thread_id: Conversation thread ID (UUID string).
        response: Agent response (Answer contract with text, agent, citations, etc.).
        language: Detected/preferred language (e.g., "pt-BR", "en-US").
        metadata: Additional metadata (citations, SQL, performance metrics, etc.).

    Validation:
        - All required fields must be present
        - message_id and thread_id must be valid UUID format
    """

    message_id: str = Field(..., description="Unique message ID (UUID)")
    thread_id: str = Field(..., description="Conversation thread ID (UUID)")
    response: Answer = Field(..., description="Agent response (Answer contract)")
    language: str = Field(..., description="Detected/preferred language")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (citations, SQL, performance metrics, etc.)",
    )

    @field_validator("message_id", "thread_id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate UUID format.

        Args:
            v: UUID string.

        Returns:
            Validated UUID string.

        Raises:
            ValueError: If not a valid UUID format.
        """
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError(f"{v} must be a valid UUID format")
        return v


class ChatHistoryResponse(BaseModel):
    """Response model for conversation history.

    Contains list of messages in a conversation thread with pagination information.

    Attributes:
        thread_id: Conversation thread ID (UUID string).
        messages: List of messages in the conversation.
            Each message: {"message_id": str, "role": str, "content": str,
                          "agent": Optional[str], "created_at": str}
        total: Total number of messages in the conversation.
        limit: Limit applied for pagination.

    Validation:
        - messages must be a list
        - total must be >= 0
        - limit must be > 0
    """

    thread_id: str = Field(..., description="Conversation thread ID (UUID)")
    messages: List[Dict[str, Any]] = Field(..., description="List of messages in the conversation")
    total: int = Field(..., description="Total number of messages", ge=0)
    limit: int = Field(..., description="Limit applied for pagination", gt=0)

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id(cls, v: str) -> str:
        """Validate thread_id is valid UUID format.

        Args:
            v: Thread ID string.

        Returns:
            Validated thread ID.

        Raises:
            ValueError: If not a valid UUID format.
        """
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("thread_id must be a valid UUID format")
        return v
