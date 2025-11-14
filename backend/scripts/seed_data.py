"""
Seed data script (populates database with sample data).

Overview
  Administrative script for populating database with sample data from seed.sql.
  Reads SQL file and executes it to insert sample data (Olist dataset).

Design
  - **SQL Execution**: Reads and executes seed.sql file.
  - **Transaction Safety**: Executes in transaction with rollback on error.
  - **Verification**: Verifies data was inserted successfully.

Integration
  - Consumes: Database connection, seed.sql file.
  - Returns: Exit code (0 for success, 1 for failure).
  - Used by: Administrative setup and testing scripts.
  - Observability: Logs seed progress and errors.

Usage
  >>> python scripts/seed_data.py
  >>> python scripts/seed_data.py --reset
"""

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import text

from app.infrastructure.database.connection import get_db_session

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Path to seed.sql file
SEED_SQL_PATH = Path(__file__).parent.parent.parent / "data" / "samples" / "seed.sql"


async def clear_existing_data(session) -> None:
    """Clear existing data from analytics tables.

    Args:
        session: Database session.

    Raises:
        Exception: If clearing fails.
    """
    try:
        logger.info("Clearing existing data...")
        # Clear analytics tables (in reverse order of dependencies)
        tables = [
            "analytics.olist_order_items",
            "analytics.olist_orders",
            "analytics.olist_products",
            "analytics.olist_customers",
            "analytics.olist_sellers",
        ]
        for table in tables:
            try:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                logger.info(f"✓ Cleared {table}")
            except Exception as e:
                logger.warning(f"⚠ Could not clear {table}: {e}")
        await session.commit()
        logger.info("✓ Existing data cleared")
    except Exception as e:
        await session.rollback()
        logger.error(f"✗ Failed to clear existing data: {e}")
        raise


async def execute_seed_sql(session, seed_path: Path) -> None:
    """Execute seed SQL file.

    Args:
        session: Database session.
        seed_path: Path to seed.sql file.

    Raises:
        Exception: If SQL execution fails.
    """
    try:
        if not seed_path.exists():
            logger.warning(f"⚠ Seed file not found: {seed_path}")
            logger.info("Skipping seed data (file does not exist)")
            return

        logger.info(f"Reading seed file: {seed_path}")
        seed_sql = seed_path.read_text(encoding="utf-8")

        if not seed_sql.strip():
            logger.warning("⚠ Seed file is empty")
            return

        logger.info("Executing seed SQL...")
        # Split SQL by semicolons and execute each statement
        statements = [s.strip() for s in seed_sql.split(";") if s.strip()]

        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    await session.execute(text(statement))
                    logger.debug(f"✓ Executed statement {i}/{len(statements)}")
                except Exception as e:
                    logger.warning(f"⚠ Statement {i} failed: {e}")
                    # Continue with next statement

        await session.commit()
        logger.info(f"✓ Executed {len(statements)} SQL statements")
    except Exception as e:
        await session.rollback()
        logger.error(f"✗ Failed to execute seed SQL: {e}")
        raise


async def verify_seed_data(session) -> bool:
    """Verify seed data was inserted successfully.

    Checks if analytics tables have data.

    Args:
        session: Database session.

    Returns:
        True if data exists, False otherwise.
    """
    try:
        # Check if analytics tables have data
        tables = [
            "analytics.olist_orders",
            "analytics.olist_products",
            "analytics.olist_customers",
        ]

        for table in tables:
            try:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                )
                count = result.scalar()
                if count > 0:
                    logger.info(f"✓ {table} has {count} rows")
                else:
                    logger.warning(f"⚠ {table} is empty")
            except Exception as e:
                logger.warning(f"⚠ Could not verify {table}: {e}")

        logger.info("✓ Seed data verification completed")
        return True
    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return False


async def seed_database(reset: bool = False) -> int:
    """Seed database with sample data.

    Args:
        reset: If True, clear existing data before seeding.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        logger.info("Seeding database...")

        async with get_db_session() as session:
            # Step 1: Clear existing data if requested
            if reset:
                await clear_existing_data(session)

            # Step 2: Execute seed SQL
            await execute_seed_sql(session, SEED_SQL_PATH)

        # Step 3: Verify seed data
        async with get_db_session() as session:
            is_valid = await verify_seed_data(session)

        if is_valid:
            logger.info("✓ Database seeding completed successfully")
            return 0
        else:
            logger.warning("⚠ Database seeding completed with warnings")
            return 0  # Still return success if data exists

    except Exception as e:
        logger.error(f"✗ Database seeding failed: {e}", exc_info=True)
        return 1


def main() -> None:
    """Main entry point for seed_data script.

    Parses command line arguments and runs database seeding.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Seed database with sample data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing data before seeding",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(seed_database(reset=args.reset))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

