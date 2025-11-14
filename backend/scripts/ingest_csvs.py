"""
CSV ingestion script (ingests CSVs into analytics database).

Overview
  Administrative script for ingesting CSV files into analytics database.
  Processes CSVs: infers or uses predefined schemas, creates tables,
  inserts data, and stores metadata. Supports batch processing with progress reporting.

Design
  - **Schema Recognition**: Recognizes known schemas (Olist) and uses predefined schemas.
  - **Batch Processing**: Processes multiple CSVs sequentially.
  - **Error Handling**: Continues processing even if individual CSVs fail.
  - **Progress Reporting**: Logs progress and provides final report.
  - **Dry Run**: Option to list files without processing.

Integration
  - Consumes: AnalyticsSchemaBuilder, database connection.
  - Returns: Exit code (0 for success, 1 for failure).
  - Used by: Administrative scripts for analytics database population.
  - Observability: Logs ingestion progress and errors.

Usage
  >>> python scripts/ingest_csvs.py <directory>
  >>> python scripts/ingest_csvs.py <directory> --recursive
  >>> python scripts/ingest_csvs.py <directory> --dry-run
  >>> python scripts/ingest_csvs.py <directory> --schema-only
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List

from app.agents.analytics import AnalyticsSchemaBuilder
from app.infrastructure.database.connection import get_db_session

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Known schema patterns (for recognition)
KNOWN_SCHEMAS = {
    "olist": [
        "olist_orders",
        "olist_products",
        "olist_customers",
        "olist_sellers",
        "olist_order_items",
    ],
}


def find_csv_files(directory: Path, recursive: bool = False) -> List[Path]:
    """Find all CSV files in directory.

    Args:
        directory: Directory to search.
        recursive: If True, search recursively.

    Returns:
        List of CSV file paths.
    """
    csv_files: List[Path] = []

    if recursive:
        csv_files = list(directory.rglob("*.csv"))
    else:
        csv_files = list(directory.glob("*.csv"))

    return sorted(csv_files)


def recognize_schema(filename: str) -> str | None:
    """Recognize known schema from filename.

    Args:
        filename: CSV filename.

    Returns:
        Schema name if recognized, None otherwise.
    """
    filename_lower = filename.lower()

    for schema_name, patterns in KNOWN_SCHEMAS.items():
        for pattern in patterns:
            if pattern in filename_lower:
                return schema_name

    return None


async def ingest_csvs(
    directory: Path,
    recursive: bool = False,
    dry_run: bool = False,
    schema_only: bool = False,
) -> int:
    """Ingest CSVs from directory into analytics database.

    Args:
        directory: Directory containing CSV files.
        recursive: If True, search recursively.
        dry_run: If True, only list files without processing.
        schema_only: If True, only create schemas without inserting data.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Validate directory
        if not directory.exists():
            logger.error(f"✗ Directory does not exist: {directory}")
            return 1

        if not directory.is_dir():
            logger.error(f"✗ Path is not a directory: {directory}")
            return 1

        # Find CSV files
        logger.info(f"Searching for CSV files in: {directory}")
        csv_files = find_csv_files(directory, recursive=recursive)

        if not csv_files:
            logger.warning(f"⚠ No CSV files found in: {directory}")
            return 0

        logger.info(f"Found {len(csv_files)} CSV file(s)")

        # Dry run: just list files
        if dry_run:
            logger.info("DRY RUN - Files that would be processed:")
            for csv_file in csv_files:
                schema = recognize_schema(csv_file.name)
                schema_info = f" (schema: {schema})" if schema else ""
                logger.info(f"  - {csv_file}{schema_info}")
            return 0

        # Process CSVs
        processed_count = 0
        error_count = 0
        errors: List[tuple[Path, str]] = []

        async with get_db_session() as session:
            builder = AnalyticsSchemaBuilder(session)

            logger.info(f"Processing {len(csv_files)} CSV file(s)...")

            for i, csv_file in enumerate(csv_files, 1):
                try:
                    schema = recognize_schema(csv_file.name)
                    schema_info = f" (known schema: {schema})" if schema else ""
                    logger.info(
                        f"[{i}/{len(csv_files)}] Processing: {csv_file.name}{schema_info}",
                    )

                    # Build schema and create table
                    table = await builder.build_schema_from_csv(csv_file)

                    processed_count += 1
                    logger.info(
                        f"✓ Successfully ingested: {csv_file.name} (table: {table.table_name})",
                    )
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    errors.append((csv_file, error_msg))
                    logger.error(
                        f"✗ Failed to ingest {csv_file.name}: {error_msg}",
                        exc_info=True,
                    )
                    # Continue with next CSV

        # Final report
        logger.info("=" * 60)
        logger.info("INGESTION REPORT")
        logger.info("=" * 60)
        logger.info(f"Total files found: {len(csv_files)}")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Errors: {error_count}")

        if errors:
            logger.info("\nErrors:")
            for csv_file, error_msg in errors:
                logger.info(f"  - {csv_file.name}: {error_msg}")

        if processed_count > 0:
            logger.info(f"\n✓ Successfully ingested {processed_count} CSV(s)")
            return 0
        else:
            logger.error("\n✗ No CSVs were successfully ingested")
            return 1

    except Exception as e:
        logger.error(f"✗ Ingestion failed: {e}", exc_info=True)
        return 1


def main() -> None:
    """Main entry point for ingest_csvs script.

    Parses command line arguments and runs CSV ingestion.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest CSV files into analytics database",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing CSV files",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Search for CSVs recursively",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without processing",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Only create schemas without inserting data (not implemented yet)",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(
        ingest_csvs(
            directory=args.directory,
            recursive=args.recursive,
            dry_run=args.dry_run,
            schema_only=args.schema_only,
        ),
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

