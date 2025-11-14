"""
Answer contracts (data contracts for agent responses).

Overview
  Defines Pydantic models for agent responses with citations, metadata,
  and performance metrics. Provides type-safe contracts for communication
  between agents and API layer.

Design
  - **Type Safety**: Pydantic models with automatic validation.
  - **Flexibility**: Optional fields for agent-specific metadata.
  - **Serialization**: Automatic JSON serialization via Pydantic.
  - **Validation**: Automatic validation of field types and constraints.

Integration
  - Consumes: None (pure data contracts).
  - Returns: Validated data models for agent responses.
  - Used by: All agents, API routes, LangGraph state.
  - Observability: N/A (data contracts only).

Usage
  >>> from app.contracts.answer import Answer, Citation
  >>> answer = Answer(
  ...     text="Response text",
  ...     agent="knowledge",
  ...     language="pt-BR",
  ...     citations=[Citation(...)]
  ... )
  >>> data = answer.model_dump()
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation from document (Knowledge Agent).

    Represents a citation to a document chunk used in the answer.
    Includes position information for highlighting in frontend.

    Attributes:
        document_id: Document ID.
        document_title: Document title.
        file_name: Original filename.
        chunk_index: Index of chunk within document.
        page_number: Page number where chunk appears (optional).
        content: Content of cited chunk.
        similarity_score: Similarity score (0.0-1.0, optional).
        start_char: Starting character position in answer text.
        end_char: Ending character position in answer text.
    """

    document_id: str = Field(..., description="Document ID")
    document_title: str = Field(..., description="Document title")
    file_name: str = Field(..., description="Original filename")
    chunk_index: int = Field(..., description="Index of chunk within document")
    page_number: Optional[int] = Field(None, description="Page number (optional)")
    content: str = Field(..., description="Content of cited chunk")
    similarity_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Similarity score (0.0-1.0, optional)",
    )
    start_char: int = Field(..., description="Starting character position in answer")
    end_char: int = Field(..., description="Ending character position in answer")


class ChunkMetadata(BaseModel):
    """Metadata for chunks used (Knowledge Agent).

    Contains metadata about document chunks retrieved and used
    for generating the answer.

    Attributes:
        chunks: List of chunks with metadata (document_id, chunk_index,
               similarity_score, content_preview).
        total_chunks: Total number of chunks returned.
        top_k: Number of chunks requested.
    """

    chunks: List[Dict[str, Any]] = Field(
        ...,
        description="List of chunks with metadata",
    )
    total_chunks: int = Field(..., description="Total number of chunks returned")
    top_k: int = Field(..., description="Number of chunks requested")


class SQLMetadata(BaseModel):
    """Metadata for generated SQL (Analytics Agent).

    Contains metadata about SQL query generated and executed
    for analytics queries.

    Attributes:
        sql: Generated SQL query.
        explanation: Explanation of the SQL query.
        tables_used: List of tables used in query.
        columns_used: List of columns used in query.
        execution_time_ms: Query execution time in milliseconds (optional).
        rows_returned: Number of rows returned (optional).
        query_plan: Query execution plan (optional).
    """

    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of SQL query")
    tables_used: List[str] = Field(..., description="List of tables used")
    columns_used: List[str] = Field(..., description="List of columns used")
    execution_time_ms: Optional[float] = Field(
        None,
        description="Query execution time in milliseconds (optional)",
    )
    rows_returned: Optional[int] = Field(
        None,
        description="Number of rows returned (optional)",
    )
    query_plan: Optional[Dict[str, Any]] = Field(
        None,
        description="Query execution plan (optional)",
    )


class DocumentMetadata(BaseModel):
    """Metadata for processed document (Commerce Agent).

    Contains metadata about document processed and analyzed
    by Commerce Agent.

    Attributes:
        document_id: Document ID.
        file_name: Original filename.
        file_type: File type (e.g., "pdf", "docx").
        schema_detected: Detected schema (JSONB structure).
        fields_extracted: List of fields extracted from document.
        confidence_score: Confidence score (0.0-1.0, optional).
        processing_time_ms: Processing time in milliseconds (optional).
    """

    document_id: str = Field(..., description="Document ID")
    file_name: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (e.g., 'pdf', 'docx')")
    schema_detected: Dict[str, Any] = Field(
        ...,
        description="Detected schema (JSONB structure)",
    )
    fields_extracted: List[str] = Field(..., description="List of extracted fields")
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0, optional)",
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Processing time in milliseconds (optional)",
    )


class PerformanceMetrics(BaseModel):
    """Performance metrics for response.

    Contains performance metrics about response generation,
    including timing and resource usage.

    Attributes:
        total_time_ms: Total processing time in milliseconds.
        retrieval_time_ms: Retrieval time in milliseconds (optional).
        generation_time_ms: LLM generation time in milliseconds (optional).
        tokens_used: Number of tokens used (optional).
        cost_estimate: Estimated cost (optional).
    """

    total_time_ms: float = Field(..., description="Total processing time in milliseconds")
    retrieval_time_ms: Optional[float] = Field(
        None,
        description="Retrieval time in milliseconds (optional)",
    )
    generation_time_ms: Optional[float] = Field(
        None,
        description="LLM generation time in milliseconds (optional)",
    )
    tokens_used: Optional[int] = Field(None, description="Number of tokens used (optional)")
    cost_estimate: Optional[float] = Field(
        None,
        description="Estimated cost (optional)",
    )


class Answer(BaseModel):
    """Main contract for agent responses.

    Represents a complete response from an agent with text, metadata,
    citations, and performance metrics. Supports agent-specific metadata
    for different agent types.

    Attributes:
        text: Response text content.
        agent: Agent that generated response ("knowledge", "analytics",
              "commerce", "triage").
        language: Response language (e.g., "pt-BR").
        citations: List of citations (Knowledge Agent, optional).
        chunk_metadata: Chunk metadata (Knowledge Agent, optional).
        sql_metadata: SQL metadata (Analytics Agent, optional).
        document_metadata: Document metadata (Commerce Agent, optional).
        performance_metrics: Performance metrics (optional).
        metadata: Additional flexible metadata (optional).
    """

    text: str = Field(..., description="Response text content")
    agent: str = Field(
        ...,
        description='Agent that generated response ("knowledge", "analytics", "commerce", "triage")',
    )
    language: str = Field(..., description="Response language (e.g., 'pt-BR')")
    citations: Optional[List[Citation]] = Field(
        None,
        description="List of citations (Knowledge Agent, optional)",
    )
    chunk_metadata: Optional[ChunkMetadata] = Field(
        None,
        description="Chunk metadata (Knowledge Agent, optional)",
    )
    sql_metadata: Optional[SQLMetadata] = Field(
        None,
        description="SQL metadata (Analytics Agent, optional)",
    )
    document_metadata: Optional[DocumentMetadata] = Field(
        None,
        description="Document metadata (Commerce Agent, optional)",
    )
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None,
        description="Performance metrics (optional)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional flexible metadata (optional)",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Answer to dictionary.

        Serializes Answer model to dictionary for JSON serialization
        or API responses. Uses Pydantic's model_dump() method.

        Returns:
            Dictionary representation of Answer.
        """
        return self.model_dump()

