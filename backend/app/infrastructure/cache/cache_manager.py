"""
Cache manager (generic cache operations with type-specific strategies).

Overview
  Provides generic cache operations (get, set, delete, clear, exists) with
  type-specific strategies for different cache types. Implements graceful
  degradation - system works without cache if Redis is unavailable.

Design
  - **Strategy Pattern**: Uses cache strategies for different data types.
  - **Graceful Degradation**: Works without cache if Redis unavailable.
  - **JSON Serialization**: Serializes/deserializes values as JSON.
  - **Type-Specific TTLs**: Each cache type has appropriate TTL from constants.

Integration
  - Consumes: Redis client, cache strategies, app.config.constants.
  - Returns: Cached values or None if not found/unavailable.
  - Used by: All agents and services that need caching.
  - Observability: Logs cache hits/misses and errors.

Usage
  >>> from app.infrastructure.cache.cache_manager import get_cache_manager
  >>> cache = get_cache_manager()
  >>> await cache.set("key", {"data": "value"}, "embeddings")
  >>> value = await cache.get("key", "embeddings")
"""

import json
import logging
from functools import lru_cache
from typing import Any, Optional

from app.infrastructure.cache.redis_client import get_redis_client
from app.infrastructure.cache.strategies import (
    EmbeddingCacheStrategy,
    LLMResponseCacheStrategy,
    RoutingCacheStrategy,
    VectorSearchCacheStrategy,
)

logger = logging.getLogger(__name__)


class CacheManager:
    """Cache manager with type-specific strategies.

    Provides generic cache operations with strategies for different
    cache types (embeddings, routing, LLM responses, vector search).
    Implements graceful degradation - continues working if Redis unavailable.

    Attributes:
        _client: Redis async client (None if Redis unavailable).
        _strategies: Dictionary of cache strategies by type.
    """

    def __init__(self) -> None:
        """Initialize cache manager.

        Gets Redis client and initializes cache strategies for all
        cache types. Client may be None if Redis unavailable.
        """
        self._client = get_redis_client()
        self._strategies: dict[str, Any] = {
            "embeddings": EmbeddingCacheStrategy(),
            "routing_decisions": RoutingCacheStrategy(),
            "llm_responses": LLMResponseCacheStrategy(),
            "vector_search_results": VectorSearchCacheStrategy(),
        }

    async def get(self, key: str, cache_type: str) -> Optional[Any]:
        """Get value from cache.

        Retrieves value from cache using appropriate strategy.
        Returns None if not found or Redis unavailable.

        Args:
            key: Cache key.
            cache_type: Type of cache ("embeddings", "routing_decisions",
                       "llm_responses", "vector_search_results").

        Returns:
            Deserialized value or None if not found/unavailable.
        """
        if self._client is None:
            return None

        try:
            strategy = self._strategies.get(cache_type)
            if not strategy:
                logger.warning(f"Unknown cache type: {cache_type}")
                return None

            cache_key = strategy.generate_key(key)
            value = await self._client.get(cache_key)

            if value is None:
                return None

            return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get error: {e}", exc_info=True)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str,
    ) -> None:
        """Set value in cache.

        Stores value in cache using appropriate strategy and TTL.
        Returns silently if Redis unavailable (graceful degradation).

        Args:
            key: Cache key.
            value: Value to cache (will be serialized as JSON).
            cache_type: Type of cache ("embeddings", "routing_decisions",
                       "llm_responses", "vector_search_results").
        """
        if self._client is None:
            return

        try:
            strategy = self._strategies.get(cache_type)
            if not strategy:
                logger.warning(f"Unknown cache type: {cache_type}")
                return

            cache_key = strategy.generate_key(key)
            ttl = strategy.get_ttl()
            serialized_value = json.dumps(value)

            await self._client.setex(cache_key, ttl, serialized_value)
        except Exception as e:
            logger.warning(f"Cache set error: {e}", exc_info=True)

    async def delete(self, key: str, cache_type: str) -> None:
        """Delete value from cache.

        Removes value from cache using appropriate strategy.
        Returns silently if Redis unavailable.

        Args:
            key: Cache key.
            cache_type: Type of cache ("embeddings", "routing_decisions",
                       "llm_responses", "vector_search_results").
        """
        if self._client is None:
            return

        try:
            strategy = self._strategies.get(cache_type)
            if not strategy:
                logger.warning(f"Unknown cache type: {cache_type}")
                return

            cache_key = strategy.generate_key(key)
            await self._client.delete(cache_key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}", exc_info=True)

    async def clear(self, cache_type: Optional[str] = None) -> None:
        """Clear cache (all or by type).

        Clears all cache or cache of specific type by deleting keys
        matching the prefix. Returns silently if Redis unavailable.

        Args:
            cache_type: Type of cache to clear (None = clear all).
        """
        if self._client is None:
            return

        try:
            if cache_type is None:
                # Clear all cache (all prefixes)
                for strategy in self._strategies.values():
                    prefix = strategy.get_prefix()
                    pattern = f"{prefix}*"
                    keys = await self._client.keys(pattern)
                    if keys:
                        await self._client.delete(*keys)
            else:
                # Clear specific cache type
                strategy = self._strategies.get(cache_type)
                if strategy:
                    prefix = strategy.get_prefix()
                    pattern = f"{prefix}*"
                    keys = await self._client.keys(pattern)
                    if keys:
                        await self._client.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache clear error: {e}", exc_info=True)

    async def exists(self, key: str, cache_type: str) -> bool:
        """Check if key exists in cache.

        Verifies if key exists in cache using appropriate strategy.
        Returns False if Redis unavailable.

        Args:
            key: Cache key.
            cache_type: Type of cache ("embeddings", "routing_decisions",
                       "llm_responses", "vector_search_results").

        Returns:
            True if key exists, False otherwise.
        """
        if self._client is None:
            return False

        try:
            strategy = self._strategies.get(cache_type)
            if not strategy:
                return False

            cache_key = strategy.generate_key(key)
            result = await self._client.exists(cache_key)
            return bool(result)
        except Exception as e:
            logger.warning(f"Cache exists error: {e}", exc_info=True)
            return False


@lru_cache()
def get_cache_manager() -> CacheManager:
    """Get singleton CacheManager instance.

    Returns cached CacheManager instance. First call creates instance,
    subsequent calls return same instance.

    Returns:
        CacheManager singleton instance.
    """
    return CacheManager()

