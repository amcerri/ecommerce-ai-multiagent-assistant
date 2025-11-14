"""
Router (semantic routing for agent selection).

Overview
  Provides semantic routing for selecting appropriate agent based on user query.
  Uses embeddings and LLM for routing decisions. CRITICAL: NEVER uses keywords
  for routing, only semantic analysis based on embeddings and LLM classification.

Design
  - **Semantic Routing**: Uses embeddings + LLM for routing decisions.
  - **NO Keywords**: NEVER uses keyword matching for routing.
  - **Caching**: Caches embeddings and routing decisions for performance.
  - **Graceful Degradation**: Falls back to triage if any step fails.

Integration
  - Consumes: LLMClient, LLMClassifier, CacheManager.
  - Returns: RouterDecision with selected agent and confidence.
  - Used by: Router node in LangGraph.
  - Observability: Logs routing decisions and errors.

Usage
  >>> from app.routing.router import Router, get_router
  >>> router = get_router()
  >>> decision = await router.route("How many orders?", "pt-BR")
"""

import hashlib
import json
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

from app.contracts.router_decision import RouterDecision
from app.infrastructure.cache.cache_manager import CacheManager
from app.infrastructure.llm.client import LLMClient
from app.routing.classifier import LLMClassifier

logger = logging.getLogger(__name__)


class Router:
    """Semantic router for agent selection.

    Routes queries to appropriate agents using semantic analysis (embeddings + LLM).
    CRITICAL: NEVER uses keywords, only semantic understanding.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        classifier: LLMClassifier,
        cache: Optional[CacheManager] = None,
    ) -> None:
        """Initialize router.

        Args:
            llm_client: LLM client for embedding generation.
            classifier: LLM classifier for semantic routing.
            cache: Cache manager for embeddings and decisions (optional).
        """
        self._llm_client = llm_client
        self._classifier = classifier
        self._cache = cache

    async def route(
        self,
        query: str,
        language: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> RouterDecision:
        """Route query to appropriate agent based on semantic analysis.

        Generates embedding, classifies query semantically, and returns routing decision.
        CRITICAL: NEVER uses keywords, only semantic understanding.

        Args:
            query: User query.
            language: Query language.
            conversation_history: Conversation history for context (optional).

        Returns:
            RouterDecision with selected agent and confidence.

        Raises:
            Exception: If routing fails (graceful degradation to triage).
        """
        try:
            # Step 1: Check cache for embedding
            query_hash = hashlib.sha256(query.encode()).hexdigest()
            embedding_cache_key = f"query_embedding:{query_hash}"

            query_embedding: Optional[List[float]] = None
            if self._cache:
                try:
                    cached_embedding = await self._cache.get(embedding_cache_key, "embeddings")
                    if cached_embedding:
                        query_embedding = cached_embedding
                        logger.info("Query embedding cache hit")
                except Exception:
                    # Graceful degradation: continue without cache
                    pass

            # Step 2: Generate embedding if not in cache
            if query_embedding is None:
                try:
                    embedding_response = await self._llm_client.generate_embedding(query)
                    query_embedding = embedding_response.embedding

                    # Cache embedding
                    if self._cache:
                        try:
                            await self._cache.set(
                                embedding_cache_key,
                                query_embedding,
                                "embeddings",
                            )
                        except Exception:
                            # Graceful degradation: continue without caching
                            pass
                except Exception as e:
                    logger.error(f"Embedding generation failed: {e}, falling back to triage")
                    # Graceful degradation: return triage decision
                    return RouterDecision(
                        agent="triage",
                        confidence=0.3,
                        reason=f"Embedding generation failed, defaulting to triage: {str(e)}",
                    )

            # Step 3: Classify query semantically
            decision = await self._classifier.classify(
                query,
                query_embedding,
                language,
                conversation_history,
            )

            logger.info(
                f"Routing decision: {decision.agent} (confidence: {decision.confidence})",
                extra={
                    "agent": decision.agent,
                    "confidence": decision.confidence,
                    "reason": decision.reason,
                },
            )

            return decision

        except Exception as e:
            logger.error(f"Routing failed: {e}, falling back to triage", exc_info=True)
            # Graceful degradation: return triage decision
            return RouterDecision(
                agent="triage",
                confidence=0.2,
                reason=f"Routing failed, defaulting to triage: {str(e)}",
            )


@lru_cache(maxsize=1)
def get_router() -> Router:
    """Get singleton Router instance.

    Creates and returns singleton Router instance with dependencies.
    Uses LRU cache to ensure only one instance is created.

    Returns:
        Singleton Router instance.
    """
    from app.infrastructure.cache import get_cache_manager
    from app.infrastructure.llm import get_llm_client

    llm_client = get_llm_client()
    cache = get_cache_manager()
    classifier = LLMClassifier(llm_client, cache)
    router = Router(llm_client, classifier, cache)

    return router
