"""
Knowledge ranker (re-ranking chunks for improved precision).

Overview
  Provides re-ranking of chunks using cross-encoder model (if available) or
  heuristic fallback. Improves precision by re-scoring chunks based on query
  relevance. Implements graceful degradation if cross-encoder unavailable.

Design
  - **Cross-Encoder**: Uses sentence-transformers CrossEncoder if available.
  - **Heuristic Fallback**: Uses keyword/phrase overlap heuristics if cross-encoder unavailable.
  - **Graceful Degradation**: Works without cross-encoder (optional feature).
  - **Top-K Selection**: Returns top RERANK_TOP_K chunks after re-ranking.

Integration
  - Consumes: constants, sentence-transformers (optional).
  - Returns: Re-ranked list of DocumentChunk objects.
  - Used by: KnowledgeAgent for re-ranking step.
  - Observability: Logs re-ranking method used (cross-encoder vs heuristic).

Usage
  >>> from app.agents.knowledge.ranker import KnowledgeRanker
  >>> ranker = KnowledgeRanker(use_cross_encoder=True)
  >>> reranked = await ranker.rerank("query", chunks)
"""

import logging
from typing import List, Optional

from app.config.constants import RERANK_TOP_K
from app.config.exceptions import SystemException
from app.infrastructure.database.models.knowledge import DocumentChunk

logger = logging.getLogger(__name__)

# Try to import CrossEncoder (optional dependency)
try:
    from sentence_transformers import CrossEncoder

    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    CrossEncoder = None  # type: ignore


class KnowledgeRanker:
    """Re-ranker for document chunks.

    Re-ranks chunks using cross-encoder (if available) or heuristic fallback.
    Improves precision by re-scoring chunks based on query relevance.
    """

    def __init__(self, use_cross_encoder: bool = False) -> None:
        """Initialize knowledge ranker.

        Args:
            use_cross_encoder: Whether to use cross-encoder (optional, graceful degradation).
        """
        self._cross_encoder: Optional[CrossEncoder] = None

        if use_cross_encoder and CROSS_ENCODER_AVAILABLE:
            try:
                # Use a lightweight cross-encoder model
                self._cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                logger.info("Cross-encoder loaded successfully")
            except Exception as e:
                logger.warning(
                    f"Failed to load cross-encoder, using heuristic fallback: {e}",
                )
                self._cross_encoder = None
        elif use_cross_encoder and not CROSS_ENCODER_AVAILABLE:
            logger.warning(
                "Cross-encoder requested but sentence-transformers not available, using heuristic fallback",
            )

    async def rerank(
        self,
        query: str,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:
        """Re-rank chunks for improved precision.

        Re-ranks chunks using cross-encoder (if available) or heuristic fallback.
        Returns top RERANK_TOP_K chunks after re-ranking.

        Args:
            query: User query text.
            chunks: List of chunks to re-rank.

        Returns:
            List of re-ranked chunks (top RERANK_TOP_K).
        """
        if not chunks:
            return []

        # Use cross-encoder if available
        if self._cross_encoder:
            return await self._rerank_with_cross_encoder(query, chunks)

        # Fallback to heuristic re-ranking
        return await self._rerank_with_heuristics(query, chunks)

    async def _rerank_with_cross_encoder(
        self,
        query: str,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:
        """Re-rank using cross-encoder model.

        Uses sentence-transformers CrossEncoder to score query-chunk pairs
        and re-ranks chunks by score.

        Args:
            query: User query text.
            chunks: List of chunks to re-rank.

        Returns:
            List of re-ranked chunks (top RERANK_TOP_K).
        """
        try:
            # Prepare query-chunk pairs
            pairs = [(query, chunk.content) for chunk in chunks]

            # Score pairs using cross-encoder
            scores = self._cross_encoder.predict(pairs)

            # Create list of (chunk, score) tuples
            chunk_scores = list(zip(chunks, scores))

            # Sort by score (descending - higher score = more relevant)
            chunk_scores.sort(key=lambda x: x[1], reverse=True)

            # Extract chunks and return top RERANK_TOP_K
            reranked_chunks = [chunk for chunk, _ in chunk_scores]
            return reranked_chunks[:RERANK_TOP_K]
        except Exception as e:
            logger.warning(
                f"Cross-encoder re-ranking failed, using heuristic fallback: {e}",
            )
            # Fallback to heuristic if cross-encoder fails
            return await self._rerank_with_heuristics(query, chunks)

    async def _rerank_with_heuristics(
        self,
        query: str,
        chunks: List[DocumentChunk],
    ) -> List[DocumentChunk]:
        """Re-rank using heuristic scoring.

        Uses keyword overlap, phrase overlap, and chunk size heuristics
        to score and re-rank chunks.

        Args:
            query: User query text.
            chunks: List of chunks to re-rank.

        Returns:
            List of re-ranked chunks (top RERANK_TOP_K).
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        chunk_scores: List[tuple[DocumentChunk, float]] = []

        for chunk in chunks:
            content_lower = chunk.content.lower()
            content_words = set(content_lower.split())

            # Calculate keyword overlap score
            keyword_overlap = len(query_words.intersection(content_words))
            keyword_score = keyword_overlap / len(query_words) if query_words else 0.0

            # Calculate phrase overlap (exact phrase matches)
            phrase_score = 0.0
            query_phrases = query_lower.split()
            for i in range(len(query_phrases) - 1):
                phrase = " ".join(query_phrases[i : i + 2])
                if phrase in content_lower:
                    phrase_score += 1.0
            phrase_score = phrase_score / max(len(query_phrases) - 1, 1)

            # Penalty for chunks that are too long or too short
            content_length = len(chunk.content)
            ideal_length = 500  # Ideal chunk length
            length_penalty = 1.0 - abs(content_length - ideal_length) / ideal_length
            length_penalty = max(0.0, min(1.0, length_penalty))

            # Combined score (weighted)
            total_score = (
                keyword_score * 0.5 + phrase_score * 0.3 + length_penalty * 0.2
            )

            chunk_scores.append((chunk, total_score))

        # Sort by score (descending)
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top RERANK_TOP_K
        reranked_chunks = [chunk for chunk, _ in chunk_scores]
        return reranked_chunks[:RERANK_TOP_K]

