"""
Cache strategies (TTL and key generation strategies for different cache types).

Overview
  Defines cache strategies with specific TTLs and key prefixes for different
  data types (embeddings, routing decisions, LLM responses, vector search results).
  Each strategy provides consistent key generation and TTL configuration.

Design
  - **Strategy Pattern**: Abstract base class with concrete implementations.
  - **TTL Configuration**: TTLs come from app.config.constants (not hardcoded).
  - **Key Hashing**: Uses hash for large keys (embeddings, long queries).
  - **Prefixes**: Descriptive prefixes for key namespacing.

Integration
  - Consumes: app.config.constants.CACHE_TTL.
  - Returns: Strategy instances for cache operations.
  - Used by: CacheManager for key generation and TTL configuration.
  - Observability: N/A (strategy classes only).

Usage
  >>> from app.infrastructure.cache.strategies import EmbeddingCacheStrategy
  >>> strategy = EmbeddingCacheStrategy()
  >>> key = strategy.generate_key("embedding_data")
  >>> ttl = strategy.get_ttl()
"""

import hashlib
from abc import ABC, abstractmethod

from app.config.constants import CACHE_TTL


class CacheStrategy(ABC):
    """Abstract base class for cache strategies.

    Defines interface for cache strategies with methods for prefix,
    TTL, and key generation. All concrete strategies must implement
    these methods.

    Methods:
        get_prefix: Return key prefix for this cache type.
        get_ttl: Return TTL in seconds for this cache type.
        generate_key: Generate complete cache key from input key.
    """

    @abstractmethod
    def get_prefix(self) -> str:
        """Get key prefix for this cache type.

        Returns:
            String prefix for cache keys (e.g., "cache:embeddings:").
        """
        pass

    @abstractmethod
    def get_ttl(self) -> int:
        """Get TTL in seconds for this cache type.

        Returns:
            TTL in seconds from CACHE_TTL constants.
        """
        pass

    @abstractmethod
    def generate_key(self, key: str) -> str:
        """Generate complete cache key from input key.

        Args:
            key: Input key (may be hashed if large).

        Returns:
            Complete cache key with prefix.
        """
        pass


class EmbeddingCacheStrategy(CacheStrategy):
    """Cache strategy for embeddings.

    Uses long TTL (30 days) since embeddings rarely change.
    Hashes keys since embeddings are large data structures.
    """

    def get_prefix(self) -> str:
        """Get prefix for embedding cache keys.

        Returns:
            Prefix "cache:embeddings:".
        """
        return "cache:embeddings:"

    def get_ttl(self) -> int:
        """Get TTL for embedding cache.

        Returns:
            TTL from CACHE_TTL["embeddings"] (30 days).
        """
        return CACHE_TTL["embeddings"]

    def generate_key(self, key: str) -> str:
        """Generate cache key for embedding.

        Hashes the input key since embeddings are large data structures.

        Args:
            key: Input key (embedding data or identifier).

        Returns:
            Complete cache key with prefix and hashed key.
        """
        prefix = self.get_prefix()
        # Hash key to avoid very long keys in Redis
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return f"{prefix}{key_hash}"


class RoutingCacheStrategy(CacheStrategy):
    """Cache strategy for routing decisions.

    Uses medium TTL (24 hours) since routing decisions are relatively stable.
    Hashes query keys to normalize and shorten them.
    """

    def get_prefix(self) -> str:
        """Get prefix for routing cache keys.

        Returns:
            Prefix "cache:routing:".
        """
        return "cache:routing:"

    def get_ttl(self) -> int:
        """Get TTL for routing cache.

        Returns:
            TTL from CACHE_TTL["routing_decisions"] (24 hours).
        """
        return CACHE_TTL["routing_decisions"]

    def generate_key(self, key: str) -> str:
        """Generate cache key for routing decision.

        Hashes the query to normalize and shorten the key.

        Args:
            key: Input key (query string).

        Returns:
            Complete cache key with prefix and hashed query.
        """
        prefix = self.get_prefix()
        # Hash query to normalize and shorten key
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return f"{prefix}{key_hash}"


class LLMResponseCacheStrategy(CacheStrategy):
    """Cache strategy for LLM responses.

    Uses short TTL (1 hour) since responses can change with context.
    Hashes query and includes model name in key generation.
    """

    def get_prefix(self) -> str:
        """Get prefix for LLM response cache keys.

        Returns:
            Prefix "cache:llm:".
        """
        return "cache:llm:"

    def get_ttl(self) -> int:
        """Get TTL for LLM response cache.

        Returns:
            TTL from CACHE_TTL["llm_responses"] (1 hour).
        """
        return CACHE_TTL["llm_responses"]

    def generate_key(self, key: str) -> str:
        """Generate cache key for LLM response.

        Hashes query and model combination to create unique key.

        Args:
            key: Input key (query + model name, or just query).

        Returns:
            Complete cache key with prefix and hashed key.
        """
        prefix = self.get_prefix()
        # Hash query + model to create unique key
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return f"{prefix}{key_hash}"


class VectorSearchCacheStrategy(CacheStrategy):
    """Cache strategy for vector search results.

    Uses short TTL (1 hour) since search results can change.
    Hashes embedding and includes top_k in key generation.
    """

    def get_prefix(self) -> str:
        """Get prefix for vector search cache keys.

        Returns:
            Prefix "cache:vector:".
        """
        return "cache:vector:"

    def get_ttl(self) -> int:
        """Get TTL for vector search cache.

        Returns:
            TTL from CACHE_TTL["vector_search_results"] (1 hour).
        """
        return CACHE_TTL["vector_search_results"]

    def generate_key(self, key: str) -> str:
        """Generate cache key for vector search result.

        Hashes embedding and top_k combination to create unique key.

        Args:
            key: Input key (embedding + top_k, or just embedding).

        Returns:
            Complete cache key with prefix and hashed key.
        """
        prefix = self.get_prefix()
        # Hash embedding + top_k to create unique key
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return f"{prefix}{key_hash}"

