"""
Router decision contracts (data contracts for routing decisions).

Overview
  Defines Pydantic models for routing decisions based on semantic analysis.
  Includes routing signals, confidence scores, and alternative agents considered.

Design
  - **Type Safety**: Pydantic models with automatic validation.
  - **Validation**: Confidence scores validated to be 0.0-1.0.
  - **Literal Types**: Agent values restricted to allowed values.
  - **Serialization**: Automatic JSON serialization via Pydantic.

Integration
  - Consumes: None (pure data contracts).
  - Returns: Validated data models for routing decisions.
  - Used by: Router, Triage Agent, LangGraph state.
  - Observability: N/A (data contracts only).

Usage
  >>> from app.contracts.router_decision import RouterDecision, RoutingSignal
  >>> decision = RouterDecision(
  ...     agent="knowledge",
  ...     confidence=0.95,
  ...     reason="Query is a knowledge question"
  ... )
  >>> data = decision.model_dump()
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RoutingSignal(BaseModel):
    """Routing signal detected during routing.

    Represents a signal detected during semantic routing analysis.
    Signals help explain routing decisions.

    Attributes:
        type: Signal type (e.g., "sql_keywords", "document_mention",
             "question_pattern").
        value: Signal value.
        confidence: Signal confidence (0.0-1.0).
    """

    type: str = Field(..., description="Signal type")
    value: str = Field(..., description="Signal value")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Signal confidence (0.0-1.0)",
    )


class RouterDecision(BaseModel):
    """Contract for routing decision.

    Represents a routing decision with selected agent, confidence,
    reason, and optional metadata about the decision process.

    Attributes:
        agent: Selected agent ("knowledge", "analytics", "commerce", "triage").
        confidence: Decision confidence (0.0-1.0).
        reason: Explanation of decision.
        query_embedding: Query embedding vector (optional, for caching).
        signals: Detected routing signals (optional).
        tables_mentioned: Tables mentioned in query (if Analytics, optional).
        alternative_agents: Alternative agents considered (optional).
    """

    agent: Literal["knowledge", "analytics", "commerce", "triage"] = Field(
        ...,
        description="Selected agent",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Decision confidence (0.0-1.0)",
    )
    reason: str = Field(..., description="Explanation of decision")
    query_embedding: Optional[List[float]] = Field(
        None,
        description="Query embedding vector (optional, for caching)",
    )
    signals: Optional[List[RoutingSignal]] = Field(
        None,
        description="Detected routing signals (optional)",
    )
    tables_mentioned: Optional[List[str]] = Field(
        None,
        description="Tables mentioned in query (if Analytics, optional)",
    )
    alternative_agents: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Alternative agents considered (optional)",
    )

    @field_validator("alternative_agents")
    @classmethod
    def validate_alternative_agents(
        cls,
        v: Optional[List[Dict[str, Any]]],
    ) -> Optional[List[Dict[str, Any]]]:
        """Validate alternative agents structure.

        Validates that each alternative agent has required fields:
        agent, confidence, reason.

        Args:
            v: Alternative agents list.

        Returns:
            Validated alternative agents list.

        Raises:
            ValueError: If structure is invalid.
        """
        if v is None:
            return v

        for alt in v:
            if not isinstance(alt, dict):
                raise ValueError("Alternative agent must be a dictionary")
            if "agent" not in alt:
                raise ValueError("Alternative agent must have 'agent' field")
            if "confidence" not in alt:
                raise ValueError("Alternative agent must have 'confidence' field")
            if "reason" not in alt:
                raise ValueError("Alternative agent must have 'reason' field")

            # Validate confidence range
            confidence = alt["confidence"]
            if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                raise ValueError("Alternative agent confidence must be between 0.0 and 1.0")

        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert RouterDecision to dictionary.

        Serializes RouterDecision model to dictionary for JSON serialization
        or API responses. Uses Pydantic's model_dump() method.

        Returns:
            Dictionary representation of RouterDecision.
        """
        return self.model_dump()

