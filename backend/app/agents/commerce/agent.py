"""
Commerce agent (document processing pipeline orchestrator).

Overview
  Main orchestrator for Commerce Agent pipeline. Coordinates document processing,
  schema detection, extraction, and analysis. Inherits from BaseAgent for common
  functionality (logging, error handling, state validation).

Design
  - **Pipeline Orchestration**: Coordinates process → detect_schema → extract → analyze.
  - **Base Agent**: Inherits from BaseAgent for common functionality.
  - **Dependency Injection**: Receives dependencies via constructor.
  - **Document Storage**: Optional document storage via repository.

Integration
  - Consumes: BaseAgent, CommerceProcessor, CommerceSchemaDetector, CommerceExtractor,
    CommerceAnalyzer, CommerceRepository, LocalStorage, LLMClient.
  - Returns: Updated GraphState with Answer containing DocumentMetadata.
  - Used by: LangGraph orchestration layer.
  - Observability: Logs via BaseAgent._log_processing.

Usage
  >>> from app.agents.commerce import CommerceAgent
  >>> agent = CommerceAgent(llm_client, storage, repository)
  >>> state = await agent.process(state)
"""

import time
from typing import Any, Optional
from uuid import uuid4

from app.agents.base import BaseAgent
from app.agents.commerce.analyzer import CommerceAnalyzer
from app.agents.commerce.extractor import CommerceExtractor
from app.agents.commerce.processor import CommerceProcessor
from app.agents.commerce.schema_detector import CommerceSchemaDetector
from app.contracts.answer import Answer, DocumentMetadata, PerformanceMetrics
from app.infrastructure.database.models.commerce import CommerceDocument
from app.infrastructure.database.repositories.commerce_repo import CommerceRepository
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.storage.local_storage import LocalStorage


class CommerceAgent(BaseAgent):
    """Commerce Agent with document processing pipeline.

    Orchestrates document processing, schema detection, extraction, and analysis
    for commerce documents. Inherits from BaseAgent for common functionality.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        storage: LocalStorage,
        repository: CommerceRepository,
    ) -> None:
        """Initialize Commerce Agent.

        Creates processor, schema_detector, extractor, and analyzer instances.

        Args:
            llm_client: LLM client for schema detection, extraction, and analysis.
            storage: Local storage for file access.
            repository: Commerce repository for document storage.
        """
        super().__init__(llm_client, name="commerce")

        # Create pipeline components
        self._processor = CommerceProcessor(storage)
        self._schema_detector = CommerceSchemaDetector(llm_client)
        self._extractor = CommerceExtractor(llm_client, self._schema_detector)
        self._analyzer = CommerceAnalyzer(llm_client)
        self._repository = repository
        self._storage = storage

    async def process(self, state: Any) -> Any:
        """Process document and generate answer.

        Implements abstract method from BaseAgent. Orchestrates pipeline:
        process → detect_schema → extract → analyze. Updates state with Answer.

        Args:
            state: Graph state with file_path, file_type, language, etc.

        Returns:
            Updated state with agent_response containing Answer.
        """
        # Step 1: Validate state
        self._validate_state(state)

        total_start_time = time.time()

        try:
            # Extract parameters from state
            file_path = getattr(state, "file_path", None)
            file_type = getattr(state, "file_type", None)
            language = getattr(state, "language", "pt-BR")

            if not file_path or not file_type:
                from app.config.exceptions import ValidationException

                raise ValidationException(
                    message="file_path and file_type are required in state",
                    details={"state": str(state)},
                )

            # Step 2: Process file
            process_start = time.time()
            process_result = await self._processor.process_file(file_path, file_type)
            process_time = (time.time() - process_start) * 1000

            text = process_result["text"]
            metadata = process_result["metadata"]

            # Step 3: Detect schema
            schema_start = time.time()
            schema = await self._schema_detector.detect_schema(text, document_type=None)
            schema_time = (time.time() - schema_start) * 1000

            # Step 4: Extract data
            extract_start = time.time()
            extract_result = await self._extractor.extract(text, schema)
            extract_time = (time.time() - extract_start) * 1000

            extracted_data = extract_result["extracted_data"]
            confidence_score = extract_result["confidence_score"]

            # Step 5: Analyze document
            analyze_start = time.time()
            analysis = await self._analyzer.analyze(extracted_data, schema)
            analyze_time = (time.time() - analyze_start) * 1000

            # Step 6: Build answer text
            answer_text = self._build_answer_text(
                extracted_data,
                analysis,
                confidence_score,
                language,
            )

            # Step 7: Create DocumentMetadata
            document_metadata = DocumentMetadata(
                schema_detected=schema,
                fields_extracted=extracted_data,
                analysis_results=analysis,
                confidence_score=confidence_score,
                processing_metadata=metadata,
            )

            # Step 8: Create PerformanceMetrics
            total_time_ms = (time.time() - total_start_time) * 1000
            performance_metrics = PerformanceMetrics(
                total_time_ms=total_time_ms,
                retrieval_time_ms=None,
                generation_time_ms=process_time + schema_time + extract_time + analyze_time,
                tokens_used=None,  # Could be extracted from LLM responses
                cost_estimate=None,
            )

            # Step 9: Create Answer
            answer = Answer(
                text=answer_text,
                agent="commerce",
                language=language,
                document_metadata=document_metadata,
                performance_metrics=performance_metrics,
            )

            # Step 10: Update state
            if hasattr(state, "agent_response"):
                state.agent_response = answer
            else:
                setattr(state, "agent_response", answer)

            # Store extracted data and schema in state for potential storage
            if not hasattr(state, "extracted_data"):
                setattr(state, "extracted_data", extracted_data)
            if not hasattr(state, "schema"):
                setattr(state, "schema", schema)

            # Step 11: Log processing
            await self._log_processing(state, answer)

            return state
        except Exception as e:
            # Use BaseAgent error handling
            return await self._handle_error(e, state)

    async def store_document(self, state: Any) -> CommerceDocument:
        """Store processed document in database.

        Stores document with extracted data and schema. Called when user
        requests document storage.

        Args:
            state: Graph state with extracted_data, schema, file_path, etc.

        Returns:
            Saved CommerceDocument.

        Raises:
            ValidationException: If required data is missing.
            DatabaseException: If storage fails.
        """
        from app.config.exceptions import ValidationException

        # Get data from state
        extracted_data = getattr(state, "extracted_data", None)
        schema = getattr(state, "schema", None)
        file_path = getattr(state, "file_path", None)
        user_id = getattr(state, "user_id", None)

        if not extracted_data or not schema:
            raise ValidationException(
                message="extracted_data and schema are required for document storage",
                details={"state": str(state)},
            )

        # Create CommerceDocument
        document = CommerceDocument(
            user_id=user_id,
            file_name=file_path.split("/")[-1] if file_path else "unknown",
            file_path=file_path or "",
            file_type=getattr(state, "file_type", "unknown"),
            extracted_data=extracted_data,
            schema_definition=schema,
            processing_metadata=getattr(state, "processing_metadata", {}),
            confidence_score=getattr(state, "confidence_score", 0.0),
        )

        # Save via repository
        saved_document = await self._repository.save_document(document)

        return saved_document

    def _build_answer_text(
        self,
        extracted_data: dict[str, Any],
        analysis: dict[str, Any],
        confidence_score: float,
        language: str,
    ) -> str:
        """Build answer text from extracted data and analysis.

        Constructs human-readable answer text summarizing document processing
        results.

        Args:
            extracted_data: Extracted data dictionary.
            analysis: Analysis results dictionary.
            confidence_score: Confidence score (0.0-1.0).
            language: Language for answer text.

        Returns:
            Formatted answer text.
        """
        if language.startswith("pt"):
            answer_parts: list[str] = [
                f"Documento processado com sucesso (confiança: {confidence_score:.0%}).",
            ]

            # Add summary if available
            summary = analysis.get("summary")
            if summary:
                answer_parts.append(f"\n{summary}")
            else:
                # Fallback: list key fields
                key_fields = list(extracted_data.keys())[:5]
                answer_parts.append(f"\nCampos extraídos: {', '.join(key_fields)}")

            # Add inconsistencies if any
            inconsistencies = analysis.get("inconsistencies", [])
            if inconsistencies:
                answer_parts.append(f"\n⚠️ {len(inconsistencies)} inconsistência(s) encontrada(s).")

            # Add risks if any
            risks = analysis.get("risks", [])
            if risks:
                answer_parts.append(f"\n⚠️ {len(risks)} risco(s) identificado(s).")

            return "\n".join(answer_parts)
        else:
            answer_parts = [
                f"Document processed successfully (confidence: {confidence_score:.0%}).",
            ]

            # Add summary if available
            summary = analysis.get("summary")
            if summary:
                answer_parts.append(f"\n{summary}")
            else:
                # Fallback: list key fields
                key_fields = list(extracted_data.keys())[:5]
                answer_parts.append(f"\nExtracted fields: {', '.join(key_fields)}")

            # Add inconsistencies if any
            inconsistencies = analysis.get("inconsistencies", [])
            if inconsistencies:
                answer_parts.append(f"\n⚠️ {len(inconsistencies)} inconsistency(ies) found.")

            # Add risks if any
            risks = analysis.get("risks", [])
            if risks:
                answer_parts.append(f"\n⚠️ {len(risks)} risk(s) identified.")

            return "\n".join(answer_parts)

