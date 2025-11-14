"""
Knowledge chunker (text chunking utilities for knowledge base).

Overview
  Provides text chunking utilities using hybrid strategy (semantic + fixed-size).
  Respects semantic boundaries (paragraphs, sentences) while ensuring chunks
  don't exceed maximum size. Applies overlap between chunks for context preservation.

Design
  - **Hybrid Strategy**: Semantic boundaries first, fixed-size fallback.
  - **Overlap**: Applies overlap between adjacent chunks.
  - **Filtering**: Filters chunks that are too small (noisy).
  - **Constants**: Uses constants from app.config.constants (not hardcoded).

Integration
  - Consumes: app.config.constants, app.utils.text.
  - Returns: List of chunk dictionaries with content and metadata.
  - Used by: KnowledgeIngester for document processing.
  - Observability: N/A (pure text processing).

Usage
  >>> from app.agents.knowledge.chunker import KnowledgeChunker
  >>> chunker = KnowledgeChunker()
  >>> chunks = chunker.chunk_text("Long text...", metadata={"page": 1})
"""

import re
from typing import Any, Dict, List, Optional

from app.config.constants import CHUNK_OVERLAP, MAX_CHUNK_SIZE, MIN_CHUNK_SIZE
from app.utils.text import extract_sentences, word_count


class KnowledgeChunker:
    """Text chunker with hybrid semantic + fixed-size strategy.

    Chunks text using semantic boundaries (paragraphs, sentences) when possible,
    falling back to fixed-size chunking for large segments. Applies overlap
    between chunks and filters chunks that are too small.
    """

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Chunk text using hybrid strategy.

        Uses semantic boundaries (paragraphs, sentences) first, then applies
        fixed-size chunking if needed. Applies overlap and filters small chunks.

        Args:
            text: Text to chunk.
            metadata: Metadata to include in each chunk (optional).

        Returns:
            List of chunk dictionaries with content, index, and metadata.
        """
        if not text or not isinstance(text, str):
            return []

        metadata = metadata or {}

        # Step 1: Split by paragraphs (semantic boundaries)
        paragraphs = self._split_paragraphs(text)

        # Step 2: Process paragraphs into chunks
        chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for paragraph in paragraphs:
            if len(paragraph) <= MAX_CHUNK_SIZE:
                # Paragraph fits in one chunk
                if len(paragraph) >= MIN_CHUNK_SIZE:
                    chunks.append(
                        {
                            "content": paragraph,
                            "index": chunk_index,
                            "metadata": metadata.copy(),
                        },
                    )
                    chunk_index += 1
            else:
                # Paragraph too large - use fixed-size chunking
                fixed_chunks = self._fixed_size_chunk(paragraph, metadata, chunk_index)
                chunks.extend(fixed_chunks)
                chunk_index += len(fixed_chunks)

        # Step 3: Apply overlap between adjacent chunks
        chunks = self._apply_overlap(chunks)

        # Step 4: Filter chunks that are too small
        chunks = [chunk for chunk in chunks if len(chunk["content"]) >= MIN_CHUNK_SIZE]

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs.

        Splits text by double newlines (paragraph boundaries) and filters
        empty paragraphs.

        Args:
            text: Text to split.

        Returns:
            List of paragraph strings.
        """
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _fixed_size_chunk(
        self,
        text: str,
        metadata: Dict[str, Any],
        start_index: int,
    ) -> List[Dict[str, Any]]:
        """Chunk text using fixed-size strategy.

        Splits text into fixed-size chunks with overlap. Used when semantic
        boundaries result in chunks that are too large.

        Args:
            text: Text to chunk.
            metadata: Metadata to include in chunks.
            start_index: Starting index for chunks.

        Returns:
            List of chunk dictionaries.
        """
        chunks: List[Dict[str, Any]] = []
        chunk_size = MAX_CHUNK_SIZE - CHUNK_OVERLAP
        index = start_index

        i = 0
        while i < len(text):
            # Calculate chunk end position
            end = min(i + chunk_size, len(text))

            # Try to break at sentence boundary if possible
            if end < len(text):
                # Look for sentence ending near chunk boundary
                sentence_end = text.rfind(".", i, end)
                if sentence_end > i + chunk_size // 2:  # Only if not too early
                    end = sentence_end + 1

            chunk_content = text[i:end].strip()
            if chunk_content:
                chunks.append(
                    {
                        "content": chunk_content,
                        "index": index,
                        "metadata": metadata.copy(),
                    },
                )
                index += 1

            # Move forward with overlap
            i = end - CHUNK_OVERLAP if end < len(text) else end

        return chunks

    def _apply_overlap(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply overlap between adjacent chunks.

        Adds overlap text from previous chunk to current chunk for context
        preservation. Overlap is added at the beginning of each chunk.

        Args:
            chunks: List of chunks to apply overlap to.

        Returns:
            List of chunks with overlap applied.
        """
        if len(chunks) <= 1:
            return chunks

        overlapped_chunks: List[Dict[str, Any]] = [chunks[0].copy()]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i].copy()

            # Get overlap text from end of previous chunk
            prev_content = prev_chunk["content"]
            if len(prev_content) > CHUNK_OVERLAP:
                overlap_text = prev_content[-CHUNK_OVERLAP:]
                # Prepend overlap to current chunk
                curr_chunk["content"] = overlap_text + " " + curr_chunk["content"]

            overlapped_chunks.append(curr_chunk)

        return overlapped_chunks

