"""
Analytics models (metadata about analytics tables).

Overview
  Defines database models for storing metadata about analytics tables.
  These models store information about table schemas, columns, and structure
  for validation and allowlist checking. The actual data tables are created
  in the analytics schema based on CSV imports.

Design
  - **Metadata Only**: These models store metadata, not the actual data tables.
  - **JSONB Schema**: Uses JSONB for flexible schema definition storage.
  - **Cascade Delete**: Deleting table metadata cascades to delete column metadata.
  - **Relationships**: Bidirectional relationships with back_populates.

Integration
  - Consumes: None (pure metadata models).
  - Returns: AnalyticsTable and AnalyticsColumn model classes.
  - Used by: Analytics agent, schema builder, allowlist validation.
  - Observability: N/A (models only).

Usage
  >>> from app.infrastructure.database.models.analytics import AnalyticsTable, AnalyticsColumn
  >>> table = AnalyticsTable(name="customers", schema_definition={...})
  >>> column = AnalyticsColumn(table_id=table.id, name="customer_id", ...)

Note:
    The actual analytics data tables (customers, orders, products, etc.)
    are created in the analytics schema by the AnalyticsSchemaBuilder when
    processing CSVs. These models only store metadata about those tables.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.models.base import BaseModel


class AnalyticsTable(BaseModel):
    """Model for analytics table metadata.

    Stores metadata about analytics tables created from CSV imports.
    This is metadata only - the actual data tables are created in the
    analytics schema by the AnalyticsSchemaBuilder.

    Attributes:
        name: Table name (e.g., "customers", "orders").
        description: Table description (optional).
        schema_definition: Complete schema definition as JSON (columns, constraints, etc.).
        source_csv: Source CSV filename (optional).
        is_active: Whether table is active.
        columns: Relationship to column metadata (one-to-many).

    Note:
        Deleting table metadata cascades to delete all column metadata.
        The actual data tables are in the analytics schema, not here.
    """

    __tablename__ = "analytics_tables"

    name = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    schema_definition = Column(JSON, nullable=False)
    source_csv = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    columns = relationship(
        "AnalyticsColumn",
        back_populates="table",
        cascade="all, delete-orphan",
    )


class AnalyticsColumn(BaseModel):
    """Model for analytics column metadata.

    Stores metadata about columns in analytics tables. This is metadata
    only - the actual columns are in the analytics schema tables.

    Attributes:
        table_id: Foreign key to parent table metadata.
        name: Column name (e.g., "customer_id", "order_status").
        data_type: PostgreSQL data type (e.g., "TEXT", "INTEGER", "NUMERIC(10,2)").
        is_nullable: Whether column accepts NULL values.
        is_primary_key: Whether column is a primary key.
        is_foreign_key: Whether column is a foreign key.
        foreign_key_reference: Foreign key reference (e.g., "customers(customer_id)").
        is_indexed: Whether column has an index.
        table: Relationship to parent table metadata (many-to-one).

    Note:
        This stores metadata about columns, not the actual columns themselves.
    """

    __tablename__ = "analytics_columns"

    table_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analytics_tables.id"),
        nullable=False,
    )
    name = Column(Text, nullable=False)
    data_type = Column(Text, nullable=False)
    is_nullable = Column(Boolean, default=True, nullable=False)
    is_primary_key = Column(Boolean, default=False, nullable=False)
    is_foreign_key = Column(Boolean, default=False, nullable=False)
    foreign_key_reference = Column(Text, nullable=True)
    is_indexed = Column(Boolean, default=False, nullable=False)

    # Relationships
    table = relationship("AnalyticsTable", back_populates="columns")

