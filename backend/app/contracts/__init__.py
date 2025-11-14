"""
Contracts module (data contracts for inter-module communication).

Overview
  Provides Pydantic models for standardized data structures used across
  the system. Includes contracts for agent responses, routing decisions,
  and supporting metadata types.

Design
  - **Type Safety**: Pydantic models with automatic validation.
  - **Standardization**: Consistent data structures across modules.
  - **Serialization**: Automatic JSON serialization via Pydantic.
  - **Validation**: Automatic validation of field types and constraints.

Integration
  - Consumes: None (pure data contracts).
  - Returns: Validated data models for system communication.
  - Used by: All agents, API routes, LangGraph state, routing.
  - Observability: N/A (data contracts only).

Usage
  >>> from app.contracts import Answer, RouterDecision, Citation
  >>> answer = Answer(text="...", agent="knowledge", language="pt-BR")
  >>> decision = RouterDecision(agent="knowledge", confidence=0.95, reason="...")
"""

# Answer Contracts
from app.contracts.answer import (
    Answer,
    ChunkMetadata,
    Citation,
    DocumentMetadata,
    PerformanceMetrics,
    SQLMetadata,
)

# Router Decision Contracts
from app.contracts.router_decision import RouterDecision, RoutingSignal

__all__ = [
    # Answer Contracts
    "Answer",
    "Citation",
    "ChunkMetadata",
    "SQLMetadata",
    "DocumentMetadata",
    "PerformanceMetrics",
    # Router Decision Contracts
    "RouterDecision",
    "RoutingSignal",
]

