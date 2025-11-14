"""
Application constants (application-wide configuration values).

Overview
  Defines all application constants that should not be hardcoded in business logic.
  All configurable values are centralized here for easy maintenance and updates.

Design
  - **Centralized Configuration**: All constants in single module for discoverability.
  - **Type Safety**: Constants use appropriate types (str, int, list, dict).
  - **Documentation**: Comments explain purpose and usage of each constant.
  - **No Hardcoding**: Business logic imports from here instead of using magic numbers/strings.

Integration
  - Consumes: None (pure constants).
  - Returns: Constants accessible via imports.
  - Used by: All application modules that need configuration values.
  - Observability: N/A (constants only).

Usage
  >>> from app.config.constants import DEFAULT_LANGUAGE, CACHE_TTL
  >>> language = DEFAULT_LANGUAGE
  >>> ttl = CACHE_TTL["embeddings"]
"""

from typing import Literal

# Language Configuration
DEFAULT_LANGUAGE: Literal["pt-BR"] = "pt-BR"
SUPPORTED_LANGUAGES: list[str] = ["pt-BR", "en-US", "es-ES", "fr-FR", "de-DE"]

# Cache TTL (in seconds)
CACHE_TTL: dict[str, int] = {
    "embeddings": 30 * 24 * 60 * 60,  # 30 days
    "routing_decisions": 24 * 60 * 60,  # 24 hours
    "llm_responses": 60 * 60,  # 1 hour
    "vector_search_results": 60 * 60,  # 1 hour
}

# Rate Limits
RATE_LIMITS: dict[str, dict[str, int]] = {
    "per_user": {"requests": 100, "window": 3600},  # 100 requests per hour
    "per_ip": {"requests": 1000, "window": 3600},  # 1000 requests per hour
    "llm_calls": {"per_user": 50, "window": 3600},  # 50 LLM calls per user per hour
}

# Chunking Configuration
MAX_CHUNK_SIZE: int = 1000  # tokens
MIN_CHUNK_SIZE: int = 100  # tokens
CHUNK_OVERLAP: int = 200  # characters

# Vector Search Configuration
VECTOR_SEARCH_TOP_K: int = 20
RERANK_TOP_K: int = 5
SIMILARITY_THRESHOLD: float = 0.7

# SQL Execution Configuration
SQL_TIMEOUT_MS: int = 30000  # 30 seconds
SQL_MAX_ROWS: int = 1000

# Document Processing Configuration
MAX_FILE_SIZE_MB: int = 10
SUPPORTED_FILE_TYPES: list[str] = ["pdf", "docx", "txt", "png", "jpg", "jpeg", "tiff"]

# Database Connection Pool Configuration
DB_POOL_SIZE: int = 20
DB_MAX_OVERFLOW: int = 10
DB_POOL_TIMEOUT: int = 30  # seconds
DB_POOL_RECYCLE: int = 3600  # 1 hour in seconds

# Embeddings Configuration
EMBEDDING_DIMENSION: int = 1536  # OpenAI text-embedding-3-small dimension

# IP Geolocation Configuration
IP_GEOLOCATION_PRIMARY_API: str = "https://get.geojs.io/v1/ip/country.json"
IP_GEOLOCATION_FALLBACK_API: str = "http://ip-api.com/json"
IP_GEOLOCATION_CACHE_TTL: int = 86400  # 24 hours in seconds

