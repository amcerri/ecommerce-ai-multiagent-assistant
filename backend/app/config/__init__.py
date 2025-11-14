"""
Configuration module (settings, exceptions, and constants).

Overview
  Centralized configuration module providing settings, exception hierarchy,
  and application constants. All configuration-related functionality is
  exported from this module for easy imports throughout the application.

Design
  - **Settings**: Pydantic-based configuration from environment variables.
  - **Exceptions**: Hierarchical exception classes for structured error handling.
  - **Constants**: Application-wide constants for configuration values.
  - **Explicit Exports**: __all__ defines all public exports.

Integration
  - Consumes: Environment variables, .env file.
  - Returns: Settings, exceptions, and constants for application use.
  - Used by: All application modules.
  - Observability: Settings include observability configuration.

Usage
  >>> from app.config import get_settings, DatabaseException, DEFAULT_LANGUAGE
  >>> settings = get_settings()
  >>> raise DatabaseException("Connection failed")
  >>> language = DEFAULT_LANGUAGE
"""

# Settings
from app.config.settings import Settings, get_settings

# Exceptions
from app.config.exceptions import (
    AppBaseException,
    AuthorizationException,
    BusinessException,
    DatabaseException,
    InvalidInputException,
    LLMException,
    NotFoundException,
    RateLimitException,
    StorageException,
    SystemException,
    UserException,
    ValidationException,
)

# Constants
from app.config.constants import (
    CACHE_TTL,
    CHUNK_OVERLAP,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT,
    DEFAULT_LANGUAGE,
    EMBEDDING_DIMENSION,
    IP_GEOLOCATION_CACHE_TTL,
    IP_GEOLOCATION_FALLBACK_API,
    IP_GEOLOCATION_PRIMARY_API,
    MAX_CHUNK_SIZE,
    MAX_FILE_SIZE_MB,
    MIN_CHUNK_SIZE,
    RATE_LIMITS,
    RERANK_TOP_K,
    SIMILARITY_THRESHOLD,
    SQL_MAX_ROWS,
    SQL_TIMEOUT_MS,
    SUPPORTED_FILE_TYPES,
    SUPPORTED_LANGUAGES,
    VECTOR_SEARCH_TOP_K,
)

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    # Exceptions - Base
    "AppBaseException",
    "SystemException",
    "BusinessException",
    "UserException",
    # Exceptions - System
    "DatabaseException",
    "LLMException",
    "StorageException",
    # Exceptions - Business
    "ValidationException",
    "AuthorizationException",
    "NotFoundException",
    # Exceptions - User
    "InvalidInputException",
    "RateLimitException",
    # Constants - Language
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    # Constants - Cache
    "CACHE_TTL",
    # Constants - Rate Limits
    "RATE_LIMITS",
    # Constants - Database Pool
    "DB_POOL_SIZE",
    "DB_MAX_OVERFLOW",
    "DB_POOL_TIMEOUT",
    "DB_POOL_RECYCLE",
    # Constants - Embeddings
    "EMBEDDING_DIMENSION",
    # Constants - IP Geolocation
    "IP_GEOLOCATION_PRIMARY_API",
    "IP_GEOLOCATION_FALLBACK_API",
    "IP_GEOLOCATION_CACHE_TTL",
    # Constants - Chunking
    "MAX_CHUNK_SIZE",
    "MIN_CHUNK_SIZE",
    "CHUNK_OVERLAP",
    # Constants - Vector Search
    "VECTOR_SEARCH_TOP_K",
    "RERANK_TOP_K",
    "SIMILARITY_THRESHOLD",
    # Constants - SQL
    "SQL_TIMEOUT_MS",
    "SQL_MAX_ROWS",
    # Constants - Document Processing
    "MAX_FILE_SIZE_MB",
    "SUPPORTED_FILE_TYPES",
]

