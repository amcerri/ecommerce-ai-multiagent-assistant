"""
Graph state (LangGraph state management).

Overview
  Defines GraphState TypedDict for LangGraph state management. State is passed
  between nodes and contains all information needed for agent processing and
  conversation management.

Design
  - **TypedDict**: Uses TypedDict for type safety and LangGraph compatibility.
  - **Serializable**: All fields are serializable for LangGraph checkpointer.
  - **Flexible**: Metadata and interrupts allow extensibility.

Integration
  - Consumes: Contracts (Answer, RouterDecision).
  - Returns: GraphState type definition.
  - Used by: All graph nodes and agents.
  - Observability: State contains thread_id and user_id for tracking.

Usage
  >>> from app.graph.state import GraphState
  >>> state: GraphState = {
  ...     "thread_id": "thread_123",
  ...     "query": "How many orders?",
  ...     "language": "pt-BR",
  ... }
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict

from app.contracts.answer import Answer
from app.contracts.router_decision import RouterDecision


class GraphState(TypedDict, total=False):
    """Graph state for LangGraph execution.

    State passed between nodes containing all information needed for
    agent processing and conversation management. All fields except
    thread_id and query are optional.

    Attributes:
        thread_id: Unique thread/conversation ID (required).
        user_id: User ID (optional, can be anonymous).
        query: User query (required).
        language: Detected/preferred language (e.g., "pt-BR", "en-US").
        router_decision: Routing decision (filled by router node).
        agent_response: Agent response (filled by selected agent).
        conversation_history: Conversation history (optional).
        metadata: Additional metadata (flexible, for extensibility).
        interrupts: Interrupts for human-in-the-loop (optional).
            Example: {"sql_approval": {"sql": "...", "status": "pending"}}
        file_path: File path for document processing (optional, for commerce agent).
        file_type: File type for document processing (optional, for commerce agent).
        extracted_data: Extracted data from document processing (optional).
        schema: Schema detected from document (optional).
        processing_metadata: Processing metadata (optional).
        confidence_score: Confidence score from extraction (optional).
        response_type: Response type from triage agent (optional).
        suggestions: Suggestions from triage agent (optional).
    """

    # Required fields
    thread_id: str
    query: str

    # Optional fields
    user_id: Optional[str]
    language: str  # Default: "pt-BR"
    router_decision: Optional[RouterDecision]
    agent_response: Optional[Answer]
    conversation_history: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    interrupts: Dict[str, Any]

    # Commerce agent specific fields
    file_path: Optional[str]
    file_type: Optional[str]
    extracted_data: Optional[Dict[str, Any]]
    schema: Optional[Dict[str, Any]]
    processing_metadata: Optional[Dict[str, Any]]
    confidence_score: Optional[float]

    # Triage agent specific fields
    response_type: Optional[str]
    suggestions: Optional[List[str]]

