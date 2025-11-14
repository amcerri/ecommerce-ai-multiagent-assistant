"""
Graph module (LangGraph state and nodes).

Overview
  Provides LangGraph state management and node implementations for orchestrating
  agent execution. GraphState defines the state structure passed between nodes,
  and nodes implement agent execution logic.

Design
  - **State Management**: GraphState TypedDict for type-safe state.
  - **Node Functions**: Async functions that receive and return GraphState.
  - **Error Handling**: Nodes handle errors gracefully without breaking execution.
  - **Dependency Injection**: Nodes obtain agent instances via singletons.

Integration
  - Consumes: Contracts, agents, router, infrastructure.
  - Returns: GraphState type and node functions.
  - Used by: LangGraph builder (Batch 16) for graph construction.
  - Observability: Logs all node executions and errors.

Usage
  >>> from app.graph import GraphState, router_node, knowledge_node
  >>> state: GraphState = {"thread_id": "123", "query": "How many orders?"}
  >>> state = await router_node(state)
  >>> state = await knowledge_node(state)
"""

from app.graph.nodes import (
    analytics_node,
    commerce_node,
    knowledge_node,
    router_node,
    triage_node,
)
from app.graph.state import GraphState

__all__ = [
    "GraphState",
    "router_node",
    "knowledge_node",
    "analytics_node",
    "commerce_node",
    "triage_node",
]

