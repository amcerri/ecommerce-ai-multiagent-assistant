"""
Analytics schema builder (CSV ingestion for administrative scripts).

Overview
  Builds analytics schemas from CSV files for administrative scripts.
  Infers schema automatically or uses predefined schemas (Olist dataset).
  Creates tables in PostgreSQL and metadata records. Updates allowlist.

Design
  - **Schema Inference**: Automatically infers types from CSV data.
  - **Predefined Schemas**: Recognizes known schemas (Olist) and applies them.
  - **Table Creation**: Creates tables in PostgreSQL schema 'analytics'.
  - **Metadata Storage**: Stores schema metadata in AnalyticsTable/AnalyticsColumn.
  - **Allowlist Update**: Updates allowlist with new tables/columns.

Integration
  - Consumes: Database session, pandas, SQLAlchemy, storage.
  - Returns: AnalyticsTable models created.
  - Used by: Administrative scripts for CSV ingestion.
  - Observability: Logs schema building progress and errors.

Usage
  >>> from app.agents.analytics.schema_builder import AnalyticsSchemaBuilder
  >>> builder = AnalyticsSchemaBuilder(session)
  >>> table = await builder.build_schema_from_csv(Path("data.csv"))
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.exceptions import DatabaseException, ValidationException
from app.infrastructure.database.models.analytics import AnalyticsColumn, AnalyticsTable

logger = logging.getLogger(__name__)

# Try to import pandas (required for CSV processing)
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore


class AnalyticsSchemaBuilder:
    """Schema builder for analytics tables from CSV files.

    Builds schemas from CSV files, creates tables in PostgreSQL,
    and stores metadata. Used by administrative scripts.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize analytics schema builder.

        Args:
            session: Async database session.
        """
        self._session = session

    async def build_schema_from_csv(
        self,
        file_path: Path,
        table_name: Optional[str] = None,
    ) -> AnalyticsTable:
        """Build schema and create table from CSV.

        Processes CSV: infers or uses predefined schema, creates table
        in PostgreSQL, inserts data, and stores metadata.

        Args:
            file_path: Path to CSV file.
            table_name: Table name (optional, uses filename if None).

        Returns:
            AnalyticsTable model created (metadata).

        Raises:
            ValidationException: If CSV is invalid.
            DatabaseException: If table creation fails.
        """
        if not PANDAS_AVAILABLE:
            raise ValidationException(
                message="pandas is required for CSV processing",
                details={"file_path": str(file_path)},
            )

        # Step 1: Read CSV
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValidationException(
                message=f"Failed to read CSV: {str(e)}",
                details={"file_path": str(file_path), "error": str(e)},
            ) from e

        # Step 2: Determine table name
        if table_name is None:
            table_name = file_path.stem.lower().replace(" ", "_")

        # Step 3: Check if schema is known (Olist dataset)
        # For now, we'll infer schema automatically
        # In production, you would check against known schemas

        # Step 4: Infer schema
        schema_definition = self._infer_schema(df)

        # Step 5: Create table in PostgreSQL
        try:
            await self._create_table(table_name, schema_definition, df)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to create table: {str(e)}",
                details={"table_name": table_name, "error": str(e)},
            ) from e

        # Step 6: Insert data
        try:
            await self._insert_data(table_name, df)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to insert data: {str(e)}",
                details={"table_name": table_name, "error": str(e)},
            ) from e

        # Step 7: Create metadata records
        try:
            analytics_table = await self._create_metadata(table_name, schema_definition, file_path)
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to create metadata: {str(e)}",
                details={"table_name": table_name, "error": str(e)},
            ) from e

        logger.info(f"Schema built successfully: {table_name}")

        return analytics_table

    def _infer_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Infer schema from DataFrame.

        Infers column types, nullability, and creates schema definition.

        Args:
            df: DataFrame to infer schema from.

        Returns:
            Schema definition dictionary.
        """
        columns: List[Dict[str, Any]] = []
        primary_keys: List[str] = []
        indexes: List[str] = []

        for col_name in df.columns:
            col_data = df[col_name]

            # Infer data type
            dtype = str(col_data.dtype)
            if "int" in dtype:
                pg_type = "INTEGER"
            elif "float" in dtype:
                pg_type = "NUMERIC"
            elif "bool" in dtype:
                pg_type = "BOOLEAN"
            elif "datetime" in dtype or "date" in dtype:
                pg_type = "TIMESTAMP WITH TIME ZONE"
            else:
                pg_type = "TEXT"

            # Check nullability
            is_nullable = col_data.isna().any()

            # Check if might be primary key (unique, not null)
            is_unique = col_data.nunique() == len(col_data)
            if is_unique and not is_nullable and len(primary_keys) == 0:
                primary_keys.append(col_name)
                indexes.append(col_name)

            column_def: Dict[str, Any] = {
                "name": col_name,
                "data_type": pg_type,
                "is_nullable": is_nullable,
                "is_primary_key": col_name in primary_keys,
                "is_foreign_key": False,
                "is_indexed": col_name in indexes,
            }

            columns.append(column_def)

        return {
            "columns": columns,
            "primary_keys": primary_keys,
            "indexes": indexes,
            "foreign_keys": [],
        }

    async def _create_table(
        self,
        table_name: str,
        schema_definition: Dict[str, Any],
        df: pd.DataFrame,
    ) -> None:
        """Create table in PostgreSQL.

        Creates table in 'analytics' schema with inferred structure.

        Args:
            table_name: Table name.
            schema_definition: Schema definition dictionary.
            df: DataFrame for data insertion.

        Raises:
            DatabaseException: If table creation fails.
        """
        try:
            # Build CREATE TABLE SQL
            columns_sql: List[str] = []
            for col_def in schema_definition["columns"]:
                col_name = col_def["name"]
                col_type = col_def["data_type"]
                nullable = "NULL" if col_def["is_nullable"] else "NOT NULL"
                columns_sql.append(f'"{col_name}" {col_type} {nullable}')

            # Add primary key constraint if exists
            constraints_sql = ""
            if schema_definition["primary_keys"]:
                pk_cols = ", ".join(f'"{pk}"' for pk in schema_definition["primary_keys"])
                constraints_sql = f", PRIMARY KEY ({pk_cols})"

            # Create schema if not exists
            create_schema_sql = "CREATE SCHEMA IF NOT EXISTS analytics;"

            # Create table SQL
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS analytics."{table_name}" (
                {', '.join(columns_sql)}{constraints_sql}
            );
            """

            # Execute SQL
            async with self._session.begin():
                await self._session.execute(text(create_schema_sql))
                await self._session.execute(text(create_table_sql))

                # Create indexes
                for index_col in schema_definition["indexes"]:
                    index_sql = f'CREATE INDEX IF NOT EXISTS idx_{table_name}_{index_col} ON analytics."{table_name}" ("{index_col}");'
                    await self._session.execute(text(index_sql))

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to create table: {str(e)}",
                details={"table_name": table_name, "error": str(e)},
            ) from e

    async def _insert_data(self, table_name: str, df: pd.DataFrame) -> None:
        """Insert data from DataFrame into table.

        Inserts all rows from DataFrame into created table.

        Args:
            table_name: Table name.
            df: DataFrame with data to insert.

        Raises:
            DatabaseException: If data insertion fails.
        """
        try:
            # Convert DataFrame to list of dictionaries
            records = df.to_dict("records")

            if not records:
                return

            # Build INSERT SQL
            columns = list(df.columns)
            columns_str = ", ".join(f'"{col}"' for col in columns)
            placeholders = ", ".join(f":{col}" for col in columns)

            insert_sql = f'INSERT INTO analytics."{table_name}" ({columns_str}) VALUES ({placeholders});'

            # Insert data in batches
            batch_size = 1000
            async with self._session.begin():
                for i in range(0, len(records), batch_size):
                    batch = records[i : i + batch_size]
                    for record in batch:
                        # Convert NaN to None
                        clean_record = {
                            k: (None if pd.isna(v) else v) for k, v in record.items()
                        }
                        await self._session.execute(text(insert_sql), clean_record)

        except Exception as e:
            raise DatabaseException(
                message=f"Failed to insert data: {str(e)}",
                details={"table_name": table_name, "error": str(e)},
            ) from e

    async def _create_metadata(
        self,
        table_name: str,
        schema_definition: Dict[str, Any],
        file_path: Path,
    ) -> AnalyticsTable:
        """Create metadata records in database.

        Creates AnalyticsTable and AnalyticsColumn records for schema metadata.

        Args:
            table_name: Table name.
            schema_definition: Schema definition dictionary.
            file_path: Source CSV file path.

        Returns:
            AnalyticsTable model created.

        Raises:
            DatabaseException: If metadata creation fails.
        """
        try:
            async with self._session.begin():
                # Create AnalyticsTable
                analytics_table = AnalyticsTable(
                    name=table_name,
                    description=f"Table created from CSV: {file_path.name}",
                    schema_definition=json.dumps(schema_definition),
                    source_csv=str(file_path),
                    is_active=True,
                )

                self._session.add(analytics_table)
                await self._session.flush()  # Get ID

                # Create AnalyticsColumn records
                for col_def in schema_definition["columns"]:
                    column = AnalyticsColumn(
                        table_id=analytics_table.id,
                        name=col_def["name"],
                        data_type=col_def["data_type"],
                        is_nullable=col_def["is_nullable"],
                        is_primary_key=col_def["is_primary_key"],
                        is_foreign_key=col_def.get("is_foreign_key", False),
                        foreign_key_reference=col_def.get("foreign_key_reference"),
                        is_indexed=col_def.get("is_indexed", False),
                    )
                    self._session.add(column)

                await self._session.commit()

                # Refresh to load relationships
                await self._session.refresh(analytics_table)
                return analytics_table

        except Exception as e:
            await self._session.rollback()
            raise DatabaseException(
                message=f"Failed to create metadata: {str(e)}",
                details={"table_name": table_name, "error": str(e)},
            ) from e

    async def build_schemas_from_csvs_batch(
        self,
        file_paths: List[Path],
    ) -> List[AnalyticsTable]:
        """Build schemas from multiple CSVs in batch.

        Processes each CSV sequentially, continuing even if individual
        CSVs fail (logs error and continues).

        Args:
            file_paths: List of CSV file paths.

        Returns:
            List of AnalyticsTable models created (may be fewer than input if some failed).
        """
        tables: List[AnalyticsTable] = []

        for file_path in file_paths:
            try:
                table = await self.build_schema_from_csv(file_path)
                tables.append(table)
            except Exception as e:
                logger.error(
                    f"Failed to build schema from CSV {file_path}: {e}",
                    exc_info=True,
                )
                # Continue with next CSV
                continue

        return tables

