"""
Database models module (all database model classes).

Overview
  Exports all database models for easy imports throughout the application.
  Models are organized by domain (knowledge, analytics, commerce, conversation).

Design
  - **Organized Exports**: Models grouped by domain for clarity.
  - **Explicit Exports**: __all__ defines all public exports.
  - **Base Classes**: Base and BaseModel exported for custom models.

Integration
  - Consumes: Base classes, SQLAlchemy, pgvector.
  - Returns: All model classes for database operations.
  - Used by: Repositories, services, API routes.
  - Observability: N/A (models only).

Usage
  >>> from app.infrastructure.database.models import Document, User, Conversation
  >>> from app.infrastructure.database.models.base import Base, BaseModel
"""

# Base
from app.infrastructure.database.models.base import Base, BaseModel

# Knowledge Models
from app.infrastructure.database.models.knowledge import Document, DocumentChunk

# Analytics Models
from app.infrastructure.database.models.analytics import (
    AnalyticsColumn,
    AnalyticsTable,
)

# Commerce Models
from app.infrastructure.database.models.commerce import CommerceDocument

# Conversation Models
from app.infrastructure.database.models.conversation import (
    Conversation,
    Message,
    User,
    UserPreferences,
)

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # Knowledge Models
    "Document",
    "DocumentChunk",
    # Analytics Models
    "AnalyticsTable",
    "AnalyticsColumn",
    # Commerce Models
    "CommerceDocument",
    # Conversation Models
    "User",
    "UserPreferences",
    "Conversation",
    "Message",
]

