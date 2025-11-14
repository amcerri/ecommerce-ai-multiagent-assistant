"""
Cache module (Redis cache manager with strategies).

Overview
  Centralized cache module providing Redis-based caching with type-specific
  strategies. Implements graceful degradation - system works without cache
  if Redis is unavailable.

Design
  - **Strategy Pattern**: Different strategies for different cache types.
  - **Graceful Degradation**: Works without cache if Redis unavailable.
  - **Type-Specific TTLs**: Each cache type has appropriate TTL from constants.
  - **JSON Serialization**: Values serialized/deserialized as JSON.

Integration
  - Consumes: Redis, app.config.settings, app.config.constants.
  - Returns: Cached values or None if not found/unavailable.
  - Used by: All agents and services that need caching.
  - Observability: Logs cache operations and errors.

Usage
  >>> from app.infrastructure.cache import get_cache_manager
  >>> cache = get_cache_manager()
  >>> await cache.set("key", value, "embeddings")
  >>> value = await cache.get("key", "embeddings")
"""

# Redis Client
from app.infrastructure.cache.redis_client import get_redis_client

# Cache Manager
from app.infrastructure.cache.cache_manager import CacheManager, get_cache_manager

# Strategies
from app.infrastructure.cache.strategies import (
    CacheStrategy,
    EmbeddingCacheStrategy,
    LLMResponseCacheStrategy,
    RoutingCacheStrategy,
    VectorSearchCacheStrategy,
)

__all__ = [
    # Redis Client
    "get_redis_client",
    # Cache Manager
    "CacheManager",
    "get_cache_manager",
    # Strategies
    "CacheStrategy",
    "EmbeddingCacheStrategy",
    "RoutingCacheStrategy",
    "LLMResponseCacheStrategy",
    "VectorSearchCacheStrategy",
]

