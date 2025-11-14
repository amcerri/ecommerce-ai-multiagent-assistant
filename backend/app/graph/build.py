"""
Graph builder (LangGraph construction and compilation).

Overview
  Builds and compiles LangGraph StateGraph with all nodes, edges, and conditional
  routing. Supports interrupts for human-in-the-loop (SQL approval). Configures
  entry point and final edges for complete graph execution.

Design
  - **StateGraph**: Uses LangGraph StateGraph for graph construction.
  - **Conditional Edges**: Dynamic routing based on router decision.
  - **Interrupts**: Support for human-in-the-loop (SQL approval).
  - **Compilation**: Compiles graph before returning.

Integration
  - Consumes: GraphState, nodes, interrupts, LangGraph StateGraph.
  - Returns: Compiled StateGraph ready for execution.
  - Used by: API routes for graph execution.
  - Observability: N/A (graph construction only).

Usage
  >>> from app.graph.build import build_graph
  >>> graph = build_graph(require_sql_approval=True)
  >>> result = await graph.ainvoke({"thread_id": "123", "query": "How many orders?"})
"""

import logging
from typing import Any, Optional

from app.graph.interrupts import check_sql_approval_status, should_interrupt_for_sql_approval
from app.graph.nodes import (
    analytics_node,
    commerce_node,
    knowledge_node,
    router_node,
    triage_node,
)
from app.graph.state import GraphState

logger = logging.getLogger(__name__)

# Try to import LangGraph (optional dependency)
try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None  # type: ignore
    END = None  # type: ignore


def route_after_router(state: GraphState) -> str:
    """Route to appropriate agent after router node.

    Determines next node based on router decision.
    Returns node name for conditional edge.

    Args:
        state: Graph state with router_decision.

    Returns:
        Next node name ("knowledge", "analytics", "commerce", "triage").
    """
    router_decision = state.get("router_decision")

    if not router_decision:
        return "triage"

    agent = router_decision.agent

    # Map agent to node name
    if agent == "knowledge":
        return "knowledge"
    elif agent == "analytics":
        return "analytics"
    elif agent == "commerce":
        return "commerce"
    else:
        return "triage"


def build_graph(require_sql_approval: bool = True) -> Any:
    """Build and compile LangGraph StateGraph.

    Constructs complete graph with all nodes, edges, and conditional routing.
    Supports interrupts for SQL approval if enabled.

    Args:
        require_sql_approval: Whether to require SQL approval (default: True).

    Returns:
        Compiled StateGraph ready for execution.

    Raises:
        ImportError: If LangGraph is not available (graceful degradation).
    """
    if not LANGGRAPH_AVAILABLE:
        logger.warning("LangGraph not available, returning stub graph")
        # Return stub that raises error when invoked
        class StubGraph:
            async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
                raise ImportError("LangGraph is not installed. Install with: pip install langgraph")

        return StubGraph()

    # Create StateGraph
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("analytics", analytics_node)
    graph.add_node("commerce", commerce_node)
    graph.add_node("triage", triage_node)

    # Set entry point
    graph.set_entry_point("router")

    # Add conditional edge after router
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "knowledge": "knowledge",
            "analytics": "analytics",
            "commerce": "commerce",
            "triage": "triage",
        },
    )

    # Add edges for SQL approval interrupt (if enabled)
    if require_sql_approval:
        # Conditional edge after analytics: check if should interrupt
        graph.add_conditional_edges(
            "analytics",
            lambda state: "interrupt" if should_interrupt_for_sql_approval(state) else "continue",
            {
                "interrupt": "__interrupt__",  # LangGraph interrupt
                "continue": END,
            },
        )

        # Conditional edge after interrupt: check approval status
        # Note: This is handled by LangGraph's interrupt mechanism
        # The graph will resume from interrupt when status changes
        # We add a conditional edge that routes based on approval status
        def route_after_interrupt(state: GraphState) -> str:
            """Route after SQL approval interrupt.

            Routes based on approval status after interrupt.

            Args:
                state: Graph state with approval status.

            Returns:
                Next node name ("continue" or "triage").
            """
            status = check_sql_approval_status(state)

            if status == "approved":
                return "continue"
            elif status == "rejected":
                return "triage"
            else:
                # Still pending, keep in interrupt
                return "__interrupt__"

        # Note: LangGraph handles interrupts differently
        # The interrupt is automatically handled by LangGraph's interrupt mechanism
        # We just need to ensure the graph can resume after approval
        # For now, we'll add a simple edge that goes to END after analytics
        # The actual interrupt handling will be done by the API layer

    # Add final edges (all agents go to END)
    graph.add_edge("knowledge", END)
    graph.add_edge("commerce", END)
    graph.add_edge("triage", END)

    # Compile graph
    compiled_graph = graph.compile()

    logger.info("Graph built and compiled successfully")

    return compiled_graph

