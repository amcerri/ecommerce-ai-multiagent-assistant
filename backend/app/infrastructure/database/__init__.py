"""
Database module (connection management and models).

Overview
  Centralized database module providing connection management, session handling,
  and all database models. Uses async SQLAlchemy with connection pooling for
  efficient database access.

Design
  - **Async Operations**: All database operations are async using asyncpg.
  - **Connection Pooling**: Configurable pool size and overflow.
  - **Session Management**: Context manager for automatic commit/rollback.
  - **Model Organization**: Models organized by domain (knowledge, analytics, commerce, conversation).

Integration
  - Consumes: app.config.settings, app.config.constants.
  - Returns: Database sessions, engine, and model classes.
  - Used by: All repository classes and database operations.
  - Observability: Connection pool metrics, query timing.

Usage
  >>> from app.infrastructure.database import get_db_session, Base, BaseModel
  >>> from app.infrastructure.database.models import Document, User
  >>> async with get_db_session() as session:
  ...     result = await session.execute(select(Document))
"""

# Connection Management
from app.infrastructure.database.connection import (
    get_db_engine,
    get_db_session,
    init_db,
)

# Base Models
from app.infrastructure.database.models.base import Base, BaseModel

__all__ = [
    # Connection Management
    "get_db_session",
    "get_db_engine",
    "init_db",
    # Base Models
    "Base",
    "BaseModel",
]

