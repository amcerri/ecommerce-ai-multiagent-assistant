"""
Redis client (async Redis client with connection pooling).

Overview
  Provides async Redis client with connection pooling and graceful degradation.
  If Redis is unavailable, the system continues to work without cache (graceful
  degradation). Client is created as singleton for efficient connection reuse.

Design
  - **Async Client**: Uses redis.asyncio for non-blocking operations.
  - **Connection Pooling**: Automatic connection pooling by redis library.
  - **Graceful Degradation**: Returns None if Redis unavailable (doesn't break app).
  - **Singleton Pattern**: Uses @lru_cache() for single client instance.

Integration
  - Consumes: app.config.settings for REDIS_URL.
  - Returns: Redis async client or None if unavailable.
  - Used by: CacheManager for cache operations.
  - Observability: Logs errors but doesn't break application.

Usage
  >>> from app.infrastructure.cache.redis_client import get_redis_client
  >>> client = get_redis_client()
  >>> if client:
  ...     await client.set("key", "value")
"""

import logging
from functools import lru_cache
from typing import Optional

import redis.asyncio as redis

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_redis_client() -> Optional[redis.Redis]:
    """Get singleton Redis async client.

    Creates and returns Redis async client with connection pooling.
    If Redis is unavailable, returns None for graceful degradation.
    Client is cached as singleton for efficient connection reuse.

    Returns:
        Redis async client or None if Redis unavailable.

    Note:
        Graceful degradation: Returns None if Redis connection fails,
        allowing system to continue without cache.
    """
    try:
        settings = get_settings()
        client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client initialized successfully")
        return client
    except Exception as e:
        logger.warning(
            f"Redis unavailable, continuing without cache: {e}",
            exc_info=True,
        )
        return None

