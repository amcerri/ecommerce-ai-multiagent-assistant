"""
Graph interrupts (human-in-the-loop helpers).

Overview
  Provides helper functions for LangGraph interrupts, especially for SQL approval
  in analytics queries. Functions are pure (no side effects) and used as conditions
  for conditional edges in the graph.

Design
  - **Pure Functions**: All functions are pure (no side effects).
  - **Type Safety**: All functions use type hints for parameters and return values.
  - **Error Handling**: Handles None values gracefully.

Integration
  - Consumes: GraphState.
  - Returns: Boolean or string values for conditional edges.
  - Used by: LangGraph builder for conditional edges.
  - Observability: N/A (pure functions).

Usage
  >>> from app.graph.interrupts import should_interrupt_for_sql_approval
  >>> if should_interrupt_for_sql_approval(state):
  ...     # Handle interrupt
"""

from typing import Dict, Any

from app.graph.state import GraphState


def should_interrupt_for_sql_approval(state: GraphState) -> bool:
    """Check if should interrupt for SQL approval.

    Verifies if execution should be interrupted for SQL approval.
    Checks if agent is analytics, SQL is present, and approval status is pending.

    Args:
        state: Graph state.

    Returns:
        True if should interrupt, False otherwise.
    """
    # Check if agent is analytics
    agent = state.get("agent")
    if agent != "analytics":
        return False

    # Check if SQL is present
    sql = state.get("sql")
    if not sql:
        return False

    # Check if approval status is pending
    interrupts = state.get("interrupts", {})
    sql_approval = interrupts.get("sql_approval", {})
    status = sql_approval.get("status")

    return status == "pending"


def check_sql_approval_status(state: GraphState) -> str:
    """Check SQL approval status.

    Retrieves SQL approval status from state interrupts.
    Returns status or "skip" if no interrupt present.

    Args:
        state: Graph state.

    Returns:
        Approval status ("pending", "approved", "rejected") or "skip" if no interrupt.
    """
    interrupts = state.get("interrupts", {})
    sql_approval = interrupts.get("sql_approval", {})

    if not sql_approval:
        return "skip"

    status = sql_approval.get("status", "skip")
    return status if status in ["pending", "approved", "rejected"] else "skip"

