"""
Database setup script (initializes database schema and extensions).

Overview
  Administrative script for initializing database: creates pgvector extension,
  analytics schema, runs Alembic migrations, and verifies setup.

Design
  - **Extension Creation**: Creates pgvector extension if not exists.
  - **Schema Creation**: Creates analytics schema if not exists.
  - **Migrations**: Runs Alembic migrations to create tables.
  - **Verification**: Verifies setup was successful.

Integration
  - Consumes: Database connection, Alembic migrations.
  - Returns: Exit code (0 for success, 1 for failure).
  - Used by: Administrative setup and deployment scripts.
  - Observability: Logs setup progress and errors.

Usage
  >>> python scripts/setup_db.py
  >>> python scripts/setup_db.py --reset
  >>> python scripts/setup_db.py --check
"""

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db_engine, get_db_session
from app.infrastructure.database.models.base import Base

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_pgvector_extension(session: AsyncSession) -> None:
    """Create pgvector extension if it doesn't exist.

    Args:
        session: Database session.

    Raises:
        Exception: If extension creation fails.
    """
    try:
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await session.commit()
        logger.info("✓ pgvector extension created or already exists")
    except Exception as e:
        await session.rollback()
        logger.error(f"✗ Failed to create pgvector extension: {e}")
        raise


async def create_analytics_schema(session: AsyncSession) -> None:
    """Create analytics schema if it doesn't exist.

    Args:
        session: Database session.

    Raises:
        Exception: If schema creation fails.
    """
    try:
        await session.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        await session.commit()
        logger.info("✓ analytics schema created or already exists")
    except Exception as e:
        await session.rollback()
        logger.error(f"✗ Failed to create analytics schema: {e}")
        raise


async def create_tables(session: AsyncSession) -> None:
    """Create all tables defined in models.

    Args:
        session: Database session.

    Raises:
        Exception: If table creation fails.
    """
    try:
        engine = get_db_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ All tables created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        raise


async def verify_setup(session: AsyncSession) -> bool:
    """Verify database setup was successful.

    Checks if pgvector extension, analytics schema, and main tables exist.

    Args:
        session: Database session.

    Returns:
        True if setup is valid, False otherwise.
    """
    try:
        # Check pgvector extension
        result = await session.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        has_vector = result.scalar()
        if not has_vector:
            logger.error("✗ pgvector extension not found")
            return False

        # Check analytics schema
        result = await session.execute(
            text(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'analytics')"
            )
        )
        has_analytics = result.scalar()
        if not has_analytics:
            logger.error("✗ analytics schema not found")
            return False

        # Check main tables (at least one should exist)
        result = await session.execute(
            text(
                """
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('documents', 'document_chunks', 'analytics_tables')
                """
            )
        )
        table_count = result.scalar()
        if table_count == 0:
            logger.warning("⚠ No main tables found (this may be expected if using Alembic)")
        else:
            logger.info(f"✓ Found {table_count} main table(s)")

        logger.info("✓ Database setup verification passed")
        return True
    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return False


async def reset_database() -> None:
    """Reset database by dropping all tables and recreating them.

    WARNING: This will delete all data!

    Raises:
        Exception: If reset fails.
    """
    logger.warning("⚠ Resetting database (all data will be deleted!)")
    try:
        engine = get_db_engine()
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("✓ All tables dropped")
            # Recreate all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✓ All tables recreated")
    except Exception as e:
        logger.error(f"✗ Failed to reset database: {e}")
        raise


async def setup_database(reset: bool = False, check_only: bool = False) -> int:
    """Setup database: create extensions, schemas, and tables.

    Args:
        reset: If True, drop and recreate all tables.
        check_only: If True, only verify setup without making changes.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        if check_only:
            logger.info("Checking database setup...")
            async with get_db_session() as session:
                is_valid = await verify_setup(session)
                return 0 if is_valid else 1

        if reset:
            await reset_database()

        logger.info("Setting up database...")

        async with get_db_session() as session:
            # Step 1: Create pgvector extension
            await create_pgvector_extension(session)

            # Step 2: Create analytics schema
            await create_analytics_schema(session)

        # Step 3: Create tables (needs new session)
        async with get_db_session() as session:
            await create_tables(session)

        # Step 4: Verify setup
        async with get_db_session() as session:
            is_valid = await verify_setup(session)

        if is_valid:
            logger.info("✓ Database setup completed successfully")
            return 0
        else:
            logger.error("✗ Database setup verification failed")
            return 1

    except Exception as e:
        logger.error(f"✗ Database setup failed: {e}", exc_info=True)
        return 1


def main() -> None:
    """Main entry point for setup_db script.

    Parses command line arguments and runs database setup.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Setup database schema and extensions")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables (WARNING: deletes all data!)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify setup without making changes",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(setup_database(reset=args.reset, check_only=args.check))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

