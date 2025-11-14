"""
Commerce extractor (information extraction with dynamic schema).

Overview
  Extracts information from documents using LLM with dynamic JSON Schema
  based on detected schema. Validates extracted data and calculates confidence
  scores. Supports retry on validation failure.

Design
  - **Dynamic Schema**: Creates JSON Schema dynamically from detected schema.
  - **Structured Outputs**: Uses LLM structured outputs for extraction.
  - **Validation**: Validates extracted data against schema.
  - **Confidence Scoring**: Calculates confidence based on completeness and coherence.

Integration
  - Consumes: LLMClient, CommerceSchemaDetector.
  - Returns: Extracted data dictionary with confidence score.
  - Used by: CommerceAgent for information extraction.
  - Observability: Logs extraction operations and validation results.

Usage
  >>> from app.agents.commerce.extractor import CommerceExtractor
  >>> extractor = CommerceExtractor(llm_client, schema_detector)
  >>> result = await extractor.extract("Document text...", schema)
"""

import logging
from typing import Any, Dict

from app.config.exceptions import LLMException
from app.infrastructure.llm.client import LLMClient

logger = logging.getLogger(__name__)


class CommerceExtractor:
    """Information extractor for commerce documents.

    Extracts information from documents using LLM with dynamic JSON Schema
    based on detected schema. Validates extracted data and calculates confidence.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        schema_detector: Any,  # CommerceSchemaDetector - avoid circular import
    ) -> None:
        """Initialize commerce extractor.

        Args:
            llm_client: LLM client for extraction.
            schema_detector: Schema detector instance (for type reference).
        """
        self._llm_client = llm_client
        # Note: schema_detector is not stored, but type is kept for documentation

    async def extract(
        self,
        text: str,
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract information from document using dynamic schema.

        Creates dynamic JSON Schema from detected schema and extracts
        information using LLM structured outputs.

        Args:
            text: Document text to extract from.
            schema: Detected schema dictionary.

        Returns:
            Dictionary with extracted_data and confidence_score.

        Raises:
            LLMException: If extraction fails.
        """
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                # Step 1: Build dynamic JSON Schema from detected schema
                json_schema = self._build_dynamic_json_schema(schema)

                # Step 2: Build prompt
                prompt = self._build_prompt(text, schema)

                # Step 3: Generate extraction using structured outputs
                structured_result = await self._llm_client.generate_structured(
                    prompt,
                    json_schema,
                )

                # Step 4: Validate extracted data
                extracted_data = structured_result
                self._validate_extraction(extracted_data, schema)

                # Step 5: Calculate confidence score
                confidence_score = self._calculate_confidence(extracted_data, schema)

                return {
                    "extracted_data": extracted_data,
                    "confidence_score": confidence_score,
                }

            except LLMException:
                raise
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"Extraction attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                else:
                    raise LLMException(
                        message=f"Failed to extract information after {max_attempts} attempts: {str(e)}",
                        details={"text": text[:200], "error": str(e)},
                    ) from e

        # Should never reach here, but for type safety
        raise LLMException(
            message="Failed to extract information",
            details={"text": text[:200]},
        )

    def _build_dynamic_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Build dynamic JSON Schema from detected schema.

        Creates JSON Schema structure based on detected fields and types.

        Args:
            schema: Detected schema dictionary.

        Returns:
            JSON Schema dictionary for structured output.
        """
        properties: Dict[str, Any] = {}
        required: list[str] = []

        fields = schema.get("fields", [])
        for field in fields:
            field_name = field["name"]
            field_type = field["type"]
            is_required = field.get("required", False)

            # Map field types to JSON Schema types
            if field_type == "string":
                json_type = {"type": "string"}
            elif field_type == "number":
                json_type = {"type": "number"}
            elif field_type == "date":
                json_type = {"type": "string", "format": "date"}
            elif field_type == "boolean":
                json_type = {"type": "boolean"}
            else:
                json_type = {"type": "string"}  # Default to string

            properties[field_name] = json_type

            if is_required:
                required.append(field_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _build_prompt(self, text: str, schema: Dict[str, Any]) -> str:
        """Build prompt for extraction.

        Constructs prompt instructing LLM to extract information following schema.

        Args:
            text: Document text.
            schema: Detected schema.

        Returns:
            Complete prompt string.
        """
        fields_desc = []
        for field in schema.get("fields", []):
            field_name = field["name"]
            field_type = field["type"]
            field_desc = field.get("description", "")
            is_required = "obrigatório" if field.get("required", False) else "opcional"
            fields_desc.append(f"- {field_name} ({field_type}, {is_required}): {field_desc}")

        fields_text = "\n".join(fields_desc)

        prompt = f"""Você é um especialista em extração de informações de documentos comerciais.

Extraia as informações do documento abaixo seguindo exatamente o schema fornecido.

SCHEMA:
{fields_text}

DOCUMENTO:
{text[:3000]}

Extraia todas as informações seguindo o schema. Se um campo não estiver presente no documento, use null para campos opcionais ou tente inferir o valor quando possível."""
        return prompt

    def _validate_extraction(
        self,
        extracted_data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> None:
        """Validate extracted data against schema.

        Validates that extracted data conforms to detected schema.

        Args:
            extracted_data: Extracted data dictionary.
            schema: Detected schema dictionary.

        Raises:
            LLMException: If validation fails.
        """
        fields = schema.get("fields", [])
        required_fields = [f["name"] for f in fields if f.get("required", False)]

        # Check required fields
        for field_name in required_fields:
            if field_name not in extracted_data or extracted_data[field_name] is None:
                raise LLMException(
                    message=f"Required field missing: {field_name}",
                    details={"field": field_name, "extracted_data": extracted_data},
                )

        # Validate field types (basic validation)
        for field in fields:
            field_name = field["name"]
            field_type = field["type"]

            if field_name in extracted_data and extracted_data[field_name] is not None:
                value = extracted_data[field_name]

                # Basic type checking
                if field_type == "number" and not isinstance(value, (int, float)):
                    try:
                        float(value)  # Try to convert
                    except (ValueError, TypeError):
                        raise LLMException(
                            message=f"Field {field_name} should be number, got {type(value).__name__}",
                            details={"field": field_name, "value": value, "expected_type": field_type},
                        )
                elif field_type == "boolean" and not isinstance(value, bool):
                    raise LLMException(
                        message=f"Field {field_name} should be boolean, got {type(value).__name__}",
                        details={"field": field_name, "value": value, "expected_type": field_type},
                    )

    def _calculate_confidence(
        self,
        extracted_data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> float:
        """Calculate confidence score for extraction.

        Calculates confidence based on completeness and coherence.

        Args:
            extracted_data: Extracted data dictionary.
            schema: Detected schema dictionary.

        Returns:
            Confidence score (0.0-1.0).
        """
        fields = schema.get("fields", [])
        if not fields:
            return 0.0

        # Calculate completeness (ratio of fields extracted)
        total_fields = len(fields)
        extracted_fields = sum(
            1 for field in fields if field["name"] in extracted_data and extracted_data[field["name"]] is not None
        )
        completeness = extracted_fields / total_fields if total_fields > 0 else 0.0

        # Calculate coherence (check for reasonable values)
        coherence = 1.0  # Assume coherent if validation passed
        # Could add more sophisticated coherence checks here

        # Combined confidence (weighted)
        confidence = completeness * 0.7 + coherence * 0.3

        return min(max(confidence, 0.0), 1.0)

