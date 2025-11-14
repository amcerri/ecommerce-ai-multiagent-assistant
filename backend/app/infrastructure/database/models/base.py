"""
Database base models (base classes for all database models).

Overview
  Defines base classes for all database models including DeclarativeBase
  and BaseModel with common fields (id, created_at, updated_at). All models
  in the system inherit from these base classes.

Design
  - **SQLAlchemy 2.0**: Uses DeclarativeBase (not declarative_base).
  - **UUID Generation**: Uses uuid4() from Python (not gen_random_uuid()).
  - **Timezone-Aware**: All timestamps use DateTime(timezone=True).
  - **Server Defaults**: Uses server_default=func.now() for automatic timestamps.

Integration
  - Consumes: sqlalchemy, uuid, datetime.
  - Returns: Base classes for database models.
  - Used by: All database models (knowledge, analytics, commerce, conversation).
  - Observability: N/A (base classes only).

Usage
  >>> from app.infrastructure.database.models.base import Base, BaseModel
  >>> class MyModel(BaseModel):
  ...     __tablename__ = "my_table"
  ...     name = Column(Text, nullable=False)
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models.

    Provides the foundation for all database models using SQLAlchemy 2.0
    DeclarativeBase. All models should inherit from this class or BaseModel.
    """

    pass


class BaseModel(Base):
    """Base model with common fields for all database models.

    Abstract base model providing common fields (id, created_at, updated_at)
    and utility methods for all database models. All concrete models should
    inherit from this class.

    Attributes:
        id: UUID primary key (generated using Python uuid4()).
        created_at: Timestamp of record creation (timezone-aware, server default).
        updated_at: Timestamp of last update (timezone-aware, auto-updated).

    Note:
        This is an abstract model (__abstract__ = True) and does not create
        a table. Concrete models must define __tablename__.
    """

    __abstract__ = True

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Iterates over all columns in the model and creates a dictionary
        with column names as keys and values as values.

        Returns:
            Dictionary with all model fields and their values.
        """
        result: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Convert UUID to string for JSON serialization
            if isinstance(value, type(uuid4())):
                value = str(value)
            # Convert datetime to ISO format string
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

