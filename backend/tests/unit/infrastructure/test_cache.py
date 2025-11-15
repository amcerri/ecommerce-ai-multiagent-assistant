"""
Unit tests for cache infrastructure.

Tests for app.infrastructure.cache.cache_manager.CacheManager.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.cache.cache_manager import CacheManager


class TestCacheManager:
    """Tests for CacheManager class."""

    @pytest.fixture
    def redis_mock(self) -> MagicMock:
        """Create mock Redis client."""
        mock = MagicMock()
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock()
        mock.delete = AsyncMock()
        mock.flushdb = AsyncMock()
        mock.exists = AsyncMock(return_value=0)
        return mock

    @patch("app.infrastructure.cache.cache_manager.get_redis_client")
    def test_init(self, mock_get_redis: MagicMock, redis_mock: MagicMock) -> None:
        """Test CacheManager initialization."""
        mock_get_redis.return_value = redis_mock
        cache = CacheManager()
        assert cache._client is not None
        assert "embeddings" in cache._strategies
        assert "routing_decisions" in cache._strategies

    @patch("app.infrastructure.cache.cache_manager.get_redis_client")
    @pytest.mark.asyncio
    async def test_get_cache_hit(
        self,
        mock_get_redis: MagicMock,
        redis_mock: MagicMock,
    ) -> None:
        """Test cache get with hit."""
        redis_mock.get = AsyncMock(return_value='{"data": "value"}')
        mock_get_redis.return_value = redis_mock
        cache = CacheManager()
        result = await cache.get("test_key", "embeddings")
        assert result == {"data": "value"}

    @patch("app.infrastructure.cache.cache_manager.get_redis_client")
    @pytest.mark.asyncio
    async def test_get_cache_miss(
        self,
        mock_get_redis: MagicMock,
        redis_mock: MagicMock,
    ) -> None:
        """Test cache get with miss."""
        redis_mock.get = AsyncMock(return_value=None)
        mock_get_redis.return_value = redis_mock
        cache = CacheManager()
        result = await cache.get("test_key", "embeddings")
        assert result is None

    @patch("app.infrastructure.cache.cache_manager.get_redis_client")
    @pytest.mark.asyncio
    async def test_set(
        self,
        mock_get_redis: MagicMock,
        redis_mock: MagicMock,
    ) -> None:
        """Test cache set."""
        mock_get_redis.return_value = redis_mock
        cache = CacheManager()
        await cache.set("test_key", {"data": "value"}, "embeddings")
        redis_mock.setex.assert_called_once()

    @patch("app.infrastructure.cache.cache_manager.get_redis_client")
    @pytest.mark.asyncio
    async def test_delete(
        self,
        mock_get_redis: MagicMock,
        redis_mock: MagicMock,
    ) -> None:
        """Test cache delete."""
        mock_get_redis.return_value = redis_mock
        cache = CacheManager()
        await cache.delete("test_key", "embeddings")
        redis_mock.delete.assert_called_once()

    @patch("app.infrastructure.cache.cache_manager.get_redis_client")
    @pytest.mark.asyncio
    async def test_graceful_degradation(
        self,
        mock_get_redis: MagicMock,
    ) -> None:
        """Test graceful degradation when Redis unavailable."""
        mock_get_redis.return_value = None
        cache = CacheManager()
        # Should not raise exception
        result = await cache.get("test_key", "embeddings")
        assert result is None
        await cache.set("test_key", {"data": "value"}, "embeddings")  # Should not raise
        await cache.delete("test_key", "embeddings")  # Should not raise

