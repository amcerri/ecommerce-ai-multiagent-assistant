"""
Conversation models (users, conversations, messages, preferences).

Overview
  Defines database models for user management, conversations, messages,
  and user preferences. Supports both authenticated and anonymous users
  for flexible usage patterns.

Design
  - **Optional User**: user_id is optional in Conversation to allow anonymous chats.
  - **Thread IDs**: thread_id and message_id are unique strings (used by LangGraph).
  - **JSONB Metadata**: Uses JSONB for flexible metadata storage.
  - **Relationships**: Bidirectional relationships with cascade deletes.

Integration
  - Consumes: None (base conversation models).
  - Returns: User, UserPreferences, Conversation, Message model classes.
  - Used by: Chat API, LangGraph state management, user management.
  - Observability: N/A (models only).

Usage
  >>> from app.infrastructure.database.models.conversation import User, Conversation, Message
  >>> user = User(email="user@example.com", name="John")
  >>> conversation = Conversation(user_id=user.id, thread_id="thread-123")
  >>> message = Message(conversation_id=conversation.id, role="user", content="Hello")
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel


class User(BaseModel):
    """Model for system users.

    Represents a user of the system. Users can be authenticated or
    anonymous (for anonymous conversations).

    Attributes:
        email: User email (unique).
        name: User name (optional).
        last_login_at: Last login timestamp (optional).
        is_active: Whether user is active.
        conversations: Relationship to conversations (one-to-many).
        preferences: Relationship to user preferences (one-to-one).
        commerce_documents: Relationship to commerce documents (one-to-many).

    Note:
        Deleting a user cascades to delete conversations and preferences.
    """

    __tablename__ = "users"

    email = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    commerce_documents = relationship(
        "CommerceDocument",
        back_populates="user",
    )


class UserPreferences(BaseModel):
    """Model for user preferences.

    Stores user preferences including language, timezone, and UI settings.
    One-to-one relationship with User.

    Attributes:
        user_id: Foreign key to user (unique, one-to-one).
        language: Preferred language (default: "pt-BR").
        auto_detect_language: Whether to auto-detect language.
        timezone: User timezone (optional).
        preferences: UI/display preferences as JSON (optional).
        user: Relationship to user (one-to-one).

    Note:
        One-to-one relationship with User (uselist=False).
    """

    __tablename__ = "user_preferences"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )
    language = Column(Text, nullable=False, default="pt-BR")
    auto_detect_language = Column(Boolean, default=True, nullable=False)
    timezone = Column(Text, nullable=True)
    preferences = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="preferences")


class Conversation(BaseModel):
    """Model for conversation threads.

    Represents a conversation/thread in the chat system. Each conversation
    has a unique thread_id used by LangGraph for state management.

    Attributes:
        user_id: Foreign key to user (optional, allows anonymous conversations).
        thread_id: Unique thread ID (used by LangGraph).
        title: Conversation title (optional, can be generated).
        user: Relationship to user (many-to-one, optional).
        messages: Relationship to messages (one-to-many).

    Note:
        Deleting a conversation cascades to delete all messages.
        user_id is optional to support anonymous conversations.
    """

    __tablename__ = "conversations"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    thread_id = Column(Text, nullable=False, unique=True)
    title = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(BaseModel):
    """Model for conversation messages.

    Represents a message in a conversation. Messages can be from users
    or assistants, and include metadata about which agent processed them.

    Attributes:
        conversation_id: Foreign key to parent conversation.
        message_id: Unique message ID (used by LangGraph).
        role: Message role ("user" or "assistant").
        content: Message content.
        agent: Agent that processed message ("knowledge", "analytics", "commerce", "triage", or None).
        meta: Message metadata as JSON (citations, SQL, chunks, metrics, etc., optional).
        conversation: Relationship to parent conversation (many-to-one).

    Note:
        Deleting a conversation cascades to delete all its messages.
        meta uses JSONB for flexible storage of citations, SQL, etc.
    """

    __tablename__ = "messages"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
    )
    message_id = Column(Text, nullable=False, unique=True)
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    agent = Column(Text, nullable=True)
    meta = Column(JSON, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

