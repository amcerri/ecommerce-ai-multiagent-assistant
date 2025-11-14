"""
LLM client factory (factory for creating LLM client instances).

Overview
  Provides factory function to create and return appropriate LLM client instance
  based on configuration. Currently supports OpenAI only. Uses singleton pattern
  for efficient client reuse. Validates configuration before creating client.

Design
  - **Factory Pattern**: Centralized client creation logic.
  - **Singleton**: Uses @lru_cache() for single client instance.
  - **Validation**: Validates API key before creating client.
  - **Extensibility**: Easy to add support for other providers (Anthropic, etc.).

Integration
  - Consumes: app.config.settings, app.infrastructure.llm.openai_client.
  - Returns: LLMClient interface instance.
  - Used by: All agents and services that need LLM capabilities.
  - Observability: Logs client creation and configuration validation.

Usage
  >>> from app.infrastructure.llm import get_llm_client
  >>> client = get_llm_client()
  >>> response = await client.generate("Hello, world!")
"""

from functools import lru_cache

from app.config.exceptions import SystemException
from app.config.settings import get_settings
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.openai_client import OpenAIClient


@lru_cache()
def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance.

    Creates and returns LLM client instance based on configuration.
    Currently supports OpenAI only. Validates API key before creating client.
    Returns cached instance on subsequent calls.

    Returns:
        LLMClient interface instance (currently OpenAIClient).

    Raises:
        SystemException: If API key not configured or provider not supported.

    Note:
        Future: Can be extended to support other providers (Anthropic, etc.)
        based on configuration.
    """
    settings = get_settings()

    # Validate OpenAI API key (required)
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        raise SystemException(
            message="OpenAI API key not configured",
            details={
                "error": "OPENAI_API_KEY must be set in environment or .env file",
            },
        )

    # Currently only OpenAI is supported
    # Future: Add support for other providers based on configuration
    try:
        client = OpenAIClient()
        return client
    except Exception as e:
        raise SystemException(
            message=f"Failed to create LLM client: {str(e)}",
            details={"error": str(e)},
        ) from e

