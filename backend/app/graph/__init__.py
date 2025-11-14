"""
Graph module (LangGraph state, nodes, and builder).

Overview
  Provides LangGraph state management, node implementations, and graph builder
  for orchestrating agent execution. GraphState defines the state structure,
  nodes implement agent execution logic, and build_graph constructs the complete graph.

Design
  - **State Management**: GraphState TypedDict for type-safe state.
  - **Node Functions**: Async functions that receive and return GraphState.
  - **Graph Builder**: Constructs and compiles LangGraph StateGraph.
  - **Error Handling**: Nodes handle errors gracefully without breaking execution.

Integration
  - Consumes: Contracts, agents, router, infrastructure, LangGraph.
  - Returns: GraphState type, node functions, and compiled graph.
  - Used by: API routes for graph execution.
  - Observability: Logs all node executions and graph construction.

Usage
  >>> from app.graph import GraphState, build_graph, router_node
  >>> state: GraphState = {"thread_id": "123", "query": "How many orders?"}
  >>> graph = build_graph()
  >>> result = await graph.ainvoke(state)
"""

from app.graph.build import build_graph, route_after_router
from app.graph.interrupts import check_sql_approval_status, should_interrupt_for_sql_approval
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
    "build_graph",
    "route_after_router",
    "should_interrupt_for_sql_approval",
    "check_sql_approval_status",
]

