"""
Application settings (environment variable configuration).

Overview
  Centralized configuration system using Pydantic Settings to load and validate
  environment variables. All application settings are defined here with type safety
  and validation. Settings are loaded from .env file or environment variables.

Design
  - **Pydantic Settings**: Uses pydantic_settings for type-safe configuration.
  - **Environment Variables**: Loads from .env file in backend root or environment.
  - **Singleton Pattern**: get_settings() returns cached singleton instance.
  - **Type Validation**: Pydantic validates all field types and values.
  - **No Hardcoding**: All values come from environment or defaults (no hardcoded secrets).

Integration
  - Consumes: Environment variables and .env file.
  - Returns: Settings instance with validated configuration.
  - Used by: All application modules that need configuration.
  - Observability: Settings include logging and tracing configuration.

Usage
  >>> from app.config.settings import get_settings
  >>> settings = get_settings()
  >>> database_url = settings.database_url
  >>> openai_model = settings.openai_model
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Provides type-safe access to all application configuration values.
    Settings are loaded from .env file in backend root or environment variables.
    All fields are validated by Pydantic for type safety.

    Attributes:
        database_url: PostgreSQL database connection URL.
        redis_url: Redis connection URL.
        rabbitmq_url: RabbitMQ connection URL.
        openai_api_key: OpenAI API key (required).
        environment: Application environment (development, staging, production).
        debug: Enable debug mode.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        openai_model: OpenAI LLM model name.
        openai_embedding_model: OpenAI embedding model name.
        api_host: API server host.
        api_port: API server port.
        storage_path: Local storage path for files.
        enable_tracing: Enable OpenTelemetry tracing.
        enable_metrics: Enable Prometheus metrics.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required fields
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    rabbitmq_url: str = Field(..., alias="RABBITMQ_URL")
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    # Optional fields with defaults
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        alias="ENVIRONMENT",
    )
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    storage_path: str = Field(default="./data/storage", alias="STORAGE_PATH")
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")


@lru_cache()
def get_settings() -> Settings:
    """Get singleton Settings instance.

    Returns cached Settings instance. First call loads settings from
    environment variables or .env file. Subsequent calls return cached instance.

    Returns:
        Settings instance with all configuration values loaded and validated.
    """
    return Settings()

