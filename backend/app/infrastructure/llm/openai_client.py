"""
OpenAI LLM client (OpenAI implementation of LLM client).

Overview
  Implements LLMClient interface for OpenAI API. Supports text generation,
  structured outputs (JSON Schema), and embeddings. Uses async OpenAI client
  for non-blocking operations. Validates embedding dimensions and handles
  errors consistently.

Design
  - **Async Client**: Uses AsyncOpenAI for non-blocking operations.
  - **Structured Outputs**: Supports JSON Schema for structured responses.
  - **Batch Processing**: Supports batch embedding generation.
  - **Error Handling**: Converts OpenAI exceptions to LLMException.
  - **Validation**: Validates embedding dimensions against constants.

Integration
  - Consumes: app.config.settings, app.config.constants, app.config.exceptions.
  - Returns: LLMResponse, EmbeddingResponse, structured dictionaries.
  - Used by: All agents that need LLM capabilities.
  - Observability: Logs API calls, token usage, errors.

Usage
  >>> from app.infrastructure.llm import get_llm_client
  >>> client = get_llm_client()
  >>> response = await client.generate("Hello, world!")
  >>> embedding = await client.generate_embedding("text to embed")
"""

import json
from typing import Any, Dict, List

from openai import AsyncOpenAI

from app.config.constants import EMBEDDING_DIMENSION
from app.config.exceptions import LLMException
from app.config.settings import get_settings
from app.infrastructure.llm.client import (
    EmbeddingResponse,
    LLMClient,
    LLMResponse,
)


class OpenAIClient(LLMClient):
    """OpenAI implementation of LLM client.

    Provides OpenAI API integration for text generation, structured outputs,
    and embeddings. Uses async client for efficient non-blocking operations.

    Attributes:
        _client: Async OpenAI client.
        _model: Default model for text generation.
        _embedding_model: Default model for embeddings.
    """

    def __init__(self) -> None:
        """Initialize OpenAI client.

        Gets settings and creates AsyncOpenAI client with API key.
        Stores model names from settings.
        """
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model
        self._embedding_model = settings.openai_embedding_model

    async def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text using OpenAI.

        Generates text response from prompt using OpenAI chat completions API.
        Supports additional parameters via kwargs (temperature, max_tokens, etc.).

        Args:
            prompt: Input prompt text.
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            LLMResponse with generated text and metadata.

        Raises:
            LLMException: If OpenAI API call fails.
        """
        try:
            # Extract parameters from kwargs
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", None)
            model = kwargs.get("model", self._model)

            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Call OpenAI API
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response data
            choice = response.choices[0]
            text = choice.message.content or ""
            finish_reason = choice.finish_reason
            tokens_used = response.usage.total_tokens if response.usage else None

            return LLMResponse(
                text=text,
                model=model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                meta={"response_id": response.id},
            )
        except Exception as e:
            raise LLMException(
                message=f"OpenAI generation failed: {str(e)}",
                details={"prompt": prompt[:100], "error": str(e)},
            ) from e

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate structured output using OpenAI JSON Schema.

        Generates structured response conforming to JSON Schema using OpenAI's
        structured outputs feature. Useful for SQL generation, schema detection, etc.

        Args:
            prompt: Input prompt text.
            schema: JSON Schema definition for structured output.
            **kwargs: Additional parameters (temperature, max_tokens, etc.).

        Returns:
            Dictionary with structured data conforming to schema.

        Raises:
            LLMException: If OpenAI API call fails or JSON is invalid.
        """
        try:
            # Extract parameters from kwargs
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", None)
            model = kwargs.get("model", self._model)

            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Build response format with JSON Schema
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_response",
                    "schema": schema,
                    "strict": True,
                },
            }

            # Call OpenAI API
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

            # Extract and parse JSON
            choice = response.choices[0]
            content = choice.message.content or "{}"

            try:
                structured_data = json.loads(content)
                return structured_data
            except json.JSONDecodeError as e:
                raise LLMException(
                    message=f"Invalid JSON in structured response: {str(e)}",
                    details={"content": content[:200], "error": str(e)},
                ) from e
        except LLMException:
            raise
        except Exception as e:
            raise LLMException(
                message=f"OpenAI structured generation failed: {str(e)}",
                details={"prompt": prompt[:100], "error": str(e)},
            ) from e

    async def generate_embedding(self, text: str) -> EmbeddingResponse:
        """Generate embedding using OpenAI.

        Generates vector embedding for text using OpenAI embeddings API.
        Validates embedding dimension against EMBEDDING_DIMENSION constant.

        Args:
            text: Input text to generate embedding for.

        Returns:
            EmbeddingResponse with embedding vector and metadata.

        Raises:
            LLMException: If OpenAI API call fails or dimension is incorrect.
        """
        try:
            # Call OpenAI API
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=text,
            )

            # Extract embedding
            embedding_data = response.data[0]
            embedding = embedding_data.embedding
            tokens_used = response.usage.total_tokens if response.usage else None

            # Validate dimension
            if len(embedding) != EMBEDDING_DIMENSION:
                raise LLMException(
                    message=f"Invalid embedding dimension: expected {EMBEDDING_DIMENSION}, got {len(embedding)}",
                    details={
                        "expected_dimension": EMBEDDING_DIMENSION,
                        "actual_dimension": len(embedding),
                        "model": self._embedding_model,
                    },
                )

            return EmbeddingResponse(
                embedding=embedding,
                model=self._embedding_model,
                tokens_used=tokens_used,
            )
        except LLMException:
            raise
        except Exception as e:
            raise LLMException(
                message=f"OpenAI embedding generation failed: {str(e)}",
                details={"text": text[:100], "error": str(e)},
            ) from e

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

        Raises:
            LLMException: If OpenAI API call fails or any embedding is invalid.
        """
        try:
            # Call OpenAI API with batch
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=texts,
            )

            # Extract embeddings
            results: List[EmbeddingResponse] = []
            tokens_used = response.usage.total_tokens if response.usage else None
            tokens_per_item = (
                tokens_used // len(texts) if tokens_used and texts else None
            )

            for embedding_data in response.data:
                embedding = embedding_data.embedding

                # Validate dimension
                if len(embedding) != EMBEDDING_DIMENSION:
                    raise LLMException(
                        message=f"Invalid embedding dimension: expected {EMBEDDING_DIMENSION}, got {len(embedding)}",
                        details={
                            "expected_dimension": EMBEDDING_DIMENSION,
                            "actual_dimension": len(embedding),
                            "model": self._embedding_model,
                        },
                    )

                results.append(
                    EmbeddingResponse(
                        embedding=embedding,
                        model=self._embedding_model,
                        tokens_used=tokens_per_item,
                    ),
                )

            return results
        except LLMException:
            raise
        except Exception as e:
            raise LLMException(
                message=f"OpenAI batch embedding generation failed: {str(e)}",
                details={"text_count": len(texts), "error": str(e)},
            ) from e

