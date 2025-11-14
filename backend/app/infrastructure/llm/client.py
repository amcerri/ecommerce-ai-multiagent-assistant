"""
LLM client interface (abstract base class for LLM clients).

Overview
  Defines abstract interface for LLM clients with methods for text generation,
  structured outputs, and embeddings. Provides type definitions for responses
  using dataclasses. All LLM client implementations must inherit from this class.

Design
  - **Abstract Interface**: Uses ABC for interface definition.
  - **Type Safety**: Response types defined as dataclasses.
  - **Extensibility**: Easy to add new LLM providers by implementing interface.
  - **Async Operations**: All methods are async for non-blocking operations.

Integration
  - Consumes: None (pure interface).
  - Returns: Response types and interface definition.
  - Used by: LLM client implementations (OpenAI, future providers).
  - Observability: N/A (interface only).

Usage
  >>> from app.infrastructure.llm.client import LLMClient, LLMResponse
  >>> class MyLLMClient(LLMClient):
  ...     async def generate(self, prompt: str, **kwargs) -> LLMResponse:
  ...         # Implementation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Response from LLM text generation.

    Contains generated text and metadata about the generation process.

    Attributes:
        text: Generated text content.
        model: Model name used for generation.
        tokens_used: Number of tokens used (optional).
        finish_reason: Reason for completion (optional, e.g., "stop", "length").
        meta: Additional metadata (optional).
    """

    text: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingResponse:
    """Response from LLM embedding generation.

    Contains embedding vector and metadata about the embedding process.

    Attributes:
        embedding: Embedding vector (list of floats).
        model: Model name used for embedding generation.
        tokens_used: Number of tokens used (optional).
    """

    embedding: List[float]
    model: str
    tokens_used: Optional[int] = None


class LLMClient(ABC):
    """Abstract base class for LLM clients.

    Defines interface for LLM operations including text generation,
    structured outputs, and embeddings. All LLM client implementations
    must inherit from this class and implement all abstract methods.

    Methods:
        generate: Generate text from prompt.
        generate_structured: Generate structured output (JSON Schema).
        generate_embedding: Generate embedding for text.
        generate_embeddings_batch: Generate embeddings for multiple texts.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from prompt.

        Generates text response from input prompt using LLM.
        Supports additional parameters via kwargs (temperature, max_tokens, etc.).

        Args:
            prompt: Input prompt text.
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            LLMResponse with generated text and metadata.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate structured output using JSON Schema.

        Generates structured response conforming to provided JSON Schema.
        Useful for SQL generation, schema detection, and other structured outputs.

        Args:
            prompt: Input prompt text.
            schema: JSON Schema definition for structured output.
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            Dictionary with structured data conforming to schema.
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> EmbeddingResponse:
        """Generate embedding for text.

        Generates vector embedding for input text using embedding model.
        Embeddings are used for semantic search and similarity matching.

        Args:
            text: Input text to generate embedding for.

        Returns:
            EmbeddingResponse with embedding vector and metadata.
        """
        pass

    @abstractmethod
    async def generate_embeddings_batch(
        self,
        texts: List[str],
    ) -> List[EmbeddingResponse]:
        """Generate embeddings for multiple texts (batch processing).

        Generates embeddings for multiple texts in a single API call.
        More efficient and economical than individual calls.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            List of EmbeddingResponse objects, one per input text.
        """
        pass

