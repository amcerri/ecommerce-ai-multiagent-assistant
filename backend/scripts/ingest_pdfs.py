"""
PDF ingestion script (ingests PDFs into knowledge base).

Overview
  Administrative script for ingesting PDF files into knowledge base.
  Processes PDFs: extracts text, chunks content, generates embeddings,
  and saves to database. Supports batch processing with progress reporting.

Design
  - **Batch Processing**: Processes multiple PDFs sequentially.
  - **Error Handling**: Continues processing even if individual PDFs fail.
  - **Progress Reporting**: Logs progress and provides final report.
  - **Dry Run**: Option to list files without processing.

Integration
  - Consumes: KnowledgeIngester, database connection, LLM client, storage.
  - Returns: Exit code (0 for success, 1 for failure).
  - Used by: Administrative scripts for knowledge base population.
  - Observability: Logs ingestion progress and errors.

Usage
  >>> python scripts/ingest_pdfs.py <directory>
  >>> python scripts/ingest_pdfs.py <directory> --recursive
  >>> python scripts/ingest_pdfs.py <directory> --dry-run
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List

from app.agents.knowledge import KnowledgeChunker, KnowledgeIngester
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.database.repositories.knowledge_repo import (
    PostgreSQLKnowledgeRepository,
)
from app.infrastructure.llm import get_llm_client
from app.infrastructure.storage import get_storage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_pdf_files(directory: Path, recursive: bool = False) -> List[Path]:
    """Find all PDF files in directory.

    Args:
        directory: Directory to search.
        recursive: If True, search recursively.

    Returns:
        List of PDF file paths.
    """
    pdf_files: List[Path] = []

    if recursive:
        pdf_files = list(directory.rglob("*.pdf"))
    else:
        pdf_files = list(directory.glob("*.pdf"))

    return sorted(pdf_files)


async def ingest_pdfs(
    directory: Path,
    recursive: bool = False,
    dry_run: bool = False,
) -> int:
    """Ingest PDFs from directory into knowledge base.

    Args:
        directory: Directory containing PDF files.
        recursive: If True, search recursively.
        dry_run: If True, only list files without processing.

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

        # Find PDF files
        logger.info(f"Searching for PDF files in: {directory}")
        pdf_files = find_pdf_files(directory, recursive=recursive)

        if not pdf_files:
            logger.warning(f"⚠ No PDF files found in: {directory}")
            return 0

        logger.info(f"Found {len(pdf_files)} PDF file(s)")

        # Dry run: just list files
        if dry_run:
            logger.info("DRY RUN - Files that would be processed:")
            for pdf_file in pdf_files:
                logger.info(f"  - {pdf_file}")
            return 0

        # Initialize dependencies
        logger.info("Initializing dependencies...")
        llm_client = get_llm_client()
        storage = get_storage()
        chunker = KnowledgeChunker()

        # Process PDFs
        processed_count = 0
        error_count = 0
        errors: List[tuple[Path, str]] = []

        async with get_db_session() as session:
            repository = PostgreSQLKnowledgeRepository(session)
            ingester = KnowledgeIngester(chunker, llm_client, repository, storage)

            logger.info(f"Processing {len(pdf_files)} PDF file(s)...")

            for i, pdf_file in enumerate(pdf_files, 1):
                try:
                    logger.info(
                        f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}",
                    )
                    document = await ingester.ingest_pdf(pdf_file)
                    processed_count += 1
                    logger.info(
                        f"✓ Successfully ingested: {pdf_file.name} (ID: {document.id})",
                    )
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    errors.append((pdf_file, error_msg))
                    logger.error(
                        f"✗ Failed to ingest {pdf_file.name}: {error_msg}",
                        exc_info=True,
                    )
                    # Continue with next PDF

        # Final report
        logger.info("=" * 60)
        logger.info("INGESTION REPORT")
        logger.info("=" * 60)
        logger.info(f"Total files found: {len(pdf_files)}")
        logger.info(f"Successfully processed: {processed_count}")
        logger.info(f"Errors: {error_count}")

        if errors:
            logger.info("\nErrors:")
            for pdf_file, error_msg in errors:
                logger.info(f"  - {pdf_file.name}: {error_msg}")

        if processed_count > 0:
            logger.info(f"\n✓ Successfully ingested {processed_count} PDF(s)")
            return 0
        else:
            logger.error("\n✗ No PDFs were successfully ingested")
            return 1

    except Exception as e:
        logger.error(f"✗ Ingestion failed: {e}", exc_info=True)
        return 1


def main() -> None:
    """Main entry point for ingest_pdfs script.

    Parses command line arguments and runs PDF ingestion.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest PDF files into knowledge base",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing PDF files",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Search for PDFs recursively",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without processing",
    )

    args = parser.parse_args()

    exit_code = asyncio.run(
        ingest_pdfs(
            directory=args.directory,
            recursive=args.recursive,
            dry_run=args.dry_run,
        ),
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

