"""
LLM module (LLM client interface and implementations).

Overview
  Provides abstract LLM client interface and OpenAI implementation. Supports
  text generation, structured outputs (JSON Schema), and embeddings. Uses
  factory pattern for client creation and singleton pattern for efficient reuse.

Design
  - **Abstract Interface**: LLMClient interface for extensibility.
  - **OpenAI Implementation**: OpenAIClient for OpenAI API integration.
  - **Factory Pattern**: Centralized client creation.
  - **Structured Outputs**: JSON Schema support for structured responses.
  - **Batch Processing**: Batch embedding generation for efficiency.

Integration
  - Consumes: app.config.settings, app.config.constants, app.config.exceptions.
  - Returns: LLMResponse, EmbeddingResponse, structured dictionaries.
  - Used by: All agents that need LLM capabilities.
  - Observability: Logs API calls, token usage, errors.

Usage
  >>> from app.infrastructure.llm import get_llm_client, LLMResponse
  >>> client = get_llm_client()
  >>> response = await client.generate("Hello, world!")
  >>> structured = await client.generate_structured(prompt, schema)
  >>> embedding = await client.generate_embedding("text")
"""

# Interface
from app.infrastructure.llm.client import (
    EmbeddingResponse,
    LLMClient,
    LLMResponse,
)

# Implementation
from app.infrastructure.llm.openai_client import OpenAIClient

# Factory
from app.infrastructure.llm.factory import get_llm_client

__all__ = [
    # Interface
    "LLMClient",
    "LLMResponse",
    "EmbeddingResponse",
    # Implementation
    "OpenAIClient",
    # Factory
    "get_llm_client",
]

