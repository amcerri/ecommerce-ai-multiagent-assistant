"""
Commerce schema detector (dynamic schema detection using LLM).

Overview
  Detects document schema dynamically using LLM with structured outputs.
  Analyzes document text and identifies fields, types, and relationships.
  Supports various commercial document types (invoices, purchase orders, etc.).

Design
  - **Dynamic Detection**: Uses LLM to detect schema from document content.
  - **Structured Outputs**: Uses JSON Schema for guaranteed structure.
  - **Type Inference**: Automatically infers field types.
  - **Validation**: Validates detected schema.

Integration
  - Consumes: LLMClient.
  - Returns: Schema definition dictionary with fields and types.
  - Used by: CommerceExtractor for extraction with detected schema.
  - Observability: Logs schema detection operations.

Usage
  >>> from app.agents.commerce.schema_detector import CommerceSchemaDetector
  >>> detector = CommerceSchemaDetector(llm_client)
  >>> schema = await detector.detect_schema("Document text...", "invoice")
"""

import logging
from typing import Any, Dict, Optional

from app.config.exceptions import LLMException
from app.infrastructure.llm.client import LLMClient

logger = logging.getLogger(__name__)


class CommerceSchemaDetector:
    """Schema detector for commerce documents.

    Detects document schema dynamically using LLM with structured outputs.
    Identifies fields, types, and relationships from document content.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize commerce schema detector.

        Args:
            llm_client: LLM client for schema detection.
        """
        self._llm_client = llm_client

    async def detect_schema(
        self,
        text: str,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Detect schema from document text.

        Uses LLM to analyze document and detect fields, types, and structure.

        Args:
            text: Document text to analyze.
            document_type: Document type hint (optional, e.g., "invoice", "purchase_order").

        Returns:
            Dictionary with detected schema (fields, types, relationships).

        Raises:
            LLMException: If schema detection fails.
        """
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                # Step 1: Build prompt
                prompt = self._build_prompt(text, document_type)

                # Step 2: Build JSON Schema for structured output
                json_schema = self._build_json_schema()

                # Step 3: Generate schema using structured outputs
                structured_result = await self._llm_client.generate_structured(
                    prompt,
                    json_schema,
                )

                # Step 4: Extract and validate schema
                fields = structured_result.get("fields", [])
                if not fields:
                    raise LLMException(
                        message="No fields detected in schema",
                        details={"text": text[:200]},
                    )

                # Step 5: Infer types and build schema
                schema = {
                    "fields": fields,
                    "document_type": document_type or structured_result.get("document_type"),
                    "relationships": structured_result.get("relationships", []),
                }

                # Step 6: Validate schema
                self._validate_schema(schema)

                return schema

            except LLMException:
                raise
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"Schema detection attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                else:
                    raise LLMException(
                        message=f"Failed to detect schema after {max_attempts} attempts: {str(e)}",
                        details={"text": text[:200], "error": str(e)},
                    ) from e

        # Should never reach here, but for type safety
        raise LLMException(
            message="Failed to detect schema",
            details={"text": text[:200]},
        )

    def _build_prompt(self, text: str, document_type: Optional[str]) -> str:
        """Build prompt for schema detection.

        Constructs prompt instructing LLM to analyze document and detect schema.

        Args:
            text: Document text.
            document_type: Document type hint (optional).

        Returns:
            Complete prompt string.
        """
        doc_type_hint = f" (tipo: {document_type})" if document_type else ""

        prompt = f"""Você é um especialista em análise de documentos comerciais.

Analise o documento abaixo e identifique todos os campos presentes, seus tipos de dados, e se são obrigatórios ou opcionais.

Tipo de documento sugerido{doc_type_hint}:
{text[:3000]}

Identifique:
1. Todos os campos presentes no documento
2. Tipo de cada campo (string, number, date, boolean)
3. Se cada campo é obrigatório ou opcional
4. Descrição de cada campo
5. Relacionamentos entre campos (se houver)

Retorne um schema estruturado com todos os campos identificados."""
        return prompt

    def _build_json_schema(self) -> Dict[str, Any]:
        """Build JSON Schema for structured output.

        Defines schema for LLM structured output with fields and types.

        Returns:
            JSON Schema dictionary.
        """
        return {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "description": "Type of document (e.g., 'invoice', 'purchase_order')",
                },
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Field name",
                            },
                            "type": {
                                "type": "string",
                                "enum": ["string", "number", "date", "boolean"],
                                "description": "Field data type",
                            },
                            "required": {
                                "type": "boolean",
                                "description": "Whether field is required",
                            },
                            "description": {
                                "type": "string",
                                "description": "Field description",
                            },
                        },
                        "required": ["name", "type", "required"],
                    },
                    "description": "List of fields in the document",
                },
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field1": {"type": "string"},
                            "field2": {"type": "string"},
                            "relationship": {"type": "string"},
                        },
                    },
                    "description": "Relationships between fields (optional)",
                },
            },
            "required": ["fields"],
        }

    def _validate_schema(self, schema: Dict[str, Any]) -> None:
        """Validate detected schema.

        Validates that schema has required structure and valid field definitions.

        Args:
            schema: Schema dictionary to validate.

        Raises:
            LLMException: If schema is invalid.
        """
        if "fields" not in schema:
            raise LLMException(
                message="Schema missing 'fields' key",
                details={"schema": schema},
            )

        fields = schema["fields"]
        if not isinstance(fields, list) or len(fields) == 0:
            raise LLMException(
                message="Schema must have at least one field",
                details={"schema": schema},
            )

        # Validate each field
        valid_types = ["string", "number", "date", "boolean"]
        for field in fields:
            if "name" not in field or not field["name"]:
                raise LLMException(
                    message="Field missing 'name'",
                    details={"field": field},
                )
            if "type" not in field or field["type"] not in valid_types:
                raise LLMException(
                    message=f"Field has invalid type: {field.get('type')}",
                    details={"field": field, "valid_types": valid_types},
                )

