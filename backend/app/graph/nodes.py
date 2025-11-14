"""
Graph nodes (LangGraph node implementations).

Overview
  Defines all nodes for LangGraph execution including router node and agent nodes.
  Nodes are async functions that receive and return GraphState. Each node
  orchestrates agent execution and handles errors gracefully.

Design
  - **Node Functions**: All nodes are async functions (state -> state).
  - **Error Handling**: Nodes handle errors gracefully without breaking graph execution.
  - **Dependency Injection**: Nodes obtain agent instances (singleton or DI).
  - **Logging**: Comprehensive logging for observability.

Integration
  - Consumes: GraphState, Router, all agents, exceptions.
  - Returns: Updated GraphState.
  - Used by: LangGraph builder (Batch 16).
  - Observability: Logs all node executions and errors.

Usage
  >>> from app.graph.nodes import router_node, knowledge_node
  >>> state = await router_node(state)
  >>> state = await knowledge_node(state)
"""

import logging
from typing import Any

from app.config.exceptions import AppBaseException
from app.contracts.answer import Answer
from app.graph.state import GraphState

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
# Agents and router will be imported when needed


async def router_node(state: GraphState) -> GraphState:
    """Router node for agent selection.

    Routes query to appropriate agent using semantic routing.
    Updates state with router_decision.

    Args:
        state: Graph state with query and language.

    Returns:
        Updated state with router_decision.
    """
    try:
        from app.routing.router import get_router

        # Get router instance (singleton)
        router = get_router()

        # Get query and language from state
        query = state.get("query", "")
        language = state.get("language", "pt-BR")
        conversation_history = state.get("conversation_history")

        # Route query
        router_decision = await router.route(query, language, conversation_history)

        # Update state
        state["router_decision"] = router_decision

        logger.info(
            f"Router decision: {router_decision.agent} (confidence: {router_decision.confidence})",
            extra={
                "thread_id": state.get("thread_id"),
                "user_id": state.get("user_id"),
                "agent": router_decision.agent,
                "confidence": router_decision.confidence,
            },
        )

        return state
    except Exception as e:
        logger.error(
            f"Router node failed: {e}",
            exc_info=True,
            extra={
                "thread_id": state.get("thread_id"),
                "user_id": state.get("user_id"),
            },
        )

        # Fallback: route to triage
        from app.contracts.router_decision import RouterDecision

        state["router_decision"] = RouterDecision(
            agent="triage",
            confidence=0.0,
            reason=f"Router failed, defaulting to triage: {str(e)}",
        )

        return state


async def knowledge_node(state: GraphState) -> GraphState:
    """Knowledge Agent node.

    Processes query using Knowledge Agent (RAG pipeline).
    Updates state with agent_response.

    Args:
        state: Graph state with query and language.

    Returns:
        Updated state with agent_response.
    """
    try:
        from app.agents.knowledge import KnowledgeAgent
        from app.infrastructure.llm import get_llm_client
        from app.infrastructure.cache import get_cache_manager
        from app.infrastructure.database.repositories import PostgreSQLKnowledgeRepository
        from app.infrastructure.database.connection import get_db_session

        # Get agent instance
        llm_client = get_llm_client()
        cache = get_cache_manager()

        # Get database session for repository
        async with get_db_session() as session:
            repository = PostgreSQLKnowledgeRepository(session)
            agent = KnowledgeAgent(llm_client, repository, cache)

            # Process state
            updated_state = await agent.process(state)

            logger.info(
                "Knowledge node completed",
                extra={
                    "thread_id": state.get("thread_id"),
                    "user_id": state.get("user_id"),
                },
            )

            return updated_state
    except Exception as e:
        logger.error(
            f"Knowledge node failed: {e}",
            exc_info=True,
            extra={
                "thread_id": state.get("thread_id"),
                "user_id": state.get("user_id"),
            },
        )

        # Create error response
        error_answer = Answer(
            text=f"Erro ao processar consulta de conhecimento: {str(e)}",
            agent="knowledge",
            language=state.get("language", "pt-BR"),
        )

        state["agent_response"] = error_answer
        return state


async def analytics_node(state: GraphState) -> GraphState:
    """Analytics Agent node.

    Processes query using Analytics Agent (SQL generation and execution).
    Updates state with agent_response.

    Args:
        state: Graph state with query and language.

    Returns:
        Updated state with agent_response.
    """
    try:
        from app.agents.analytics import AnalyticsAgent
        from app.infrastructure.llm import get_llm_client
        from app.infrastructure.cache import get_cache_manager
        from app.infrastructure.database.repositories import PostgreSQLAnalyticsRepository
        from app.infrastructure.database.connection import get_db_session
        from app.routing.allowlist import AllowlistValidator

        # Get agent instance
        llm_client = get_llm_client()
        cache = get_cache_manager()
        allowlist_validator = AllowlistValidator()

        # Get database session for repository
        async with get_db_session() as session:
            repository = PostgreSQLAnalyticsRepository(session)
            agent = AnalyticsAgent(llm_client, repository, allowlist_validator, cache)

            # Process state
            updated_state = await agent.process(state)

            # Store SQL in state for interrupt (if present in response)
            if updated_state.get("agent_response"):
                sql_metadata = updated_state["agent_response"].sql_metadata
                if sql_metadata and sql_metadata.sql:
                    updated_state["sql"] = sql_metadata.sql
                    updated_state["agent"] = "analytics"

            logger.info(
                "Analytics node completed",
                extra={
                    "thread_id": state.get("thread_id"),
                    "user_id": state.get("user_id"),
                },
            )

            return updated_state
    except Exception as e:
        logger.error(
            f"Analytics node failed: {e}",
            exc_info=True,
            extra={
                "thread_id": state.get("thread_id"),
                "user_id": state.get("user_id"),
            },
        )

        # Create error response
        error_answer = Answer(
            text=f"Erro ao processar consulta de analytics: {str(e)}",
            agent="analytics",
            language=state.get("language", "pt-BR"),
        )

        state["agent_response"] = error_answer
        return state


async def commerce_node(state: GraphState) -> GraphState:
    """Commerce Agent node.

    Processes document using Commerce Agent (document processing pipeline).
    Updates state with agent_response.

    Args:
        state: Graph state with file_path, file_type, and language.

    Returns:
        Updated state with agent_response.
    """
    try:
        from app.agents.commerce import CommerceAgent
        from app.infrastructure.llm import get_llm_client
        from app.infrastructure.storage import get_storage
        from app.infrastructure.database.repositories import PostgreSQLCommerceRepository
        from app.infrastructure.database.connection import get_db_session

        # Get agent instance
        llm_client = get_llm_client()
        storage = get_storage()

        # Get database session for repository
        async with get_db_session() as session:
            repository = PostgreSQLCommerceRepository(session)
            agent = CommerceAgent(llm_client, storage, repository)

            # Process state
            updated_state = await agent.process(state)

            logger.info(
                "Commerce node completed",
                extra={
                    "thread_id": state.get("thread_id"),
                    "user_id": state.get("user_id"),
                },
            )

            return updated_state
    except Exception as e:
        logger.error(
            f"Commerce node failed: {e}",
            exc_info=True,
            extra={
                "thread_id": state.get("thread_id"),
                "user_id": state.get("user_id"),
            },
        )

        # Create error response
        error_answer = Answer(
            text=f"Erro ao processar documento comercial: {str(e)}",
            agent="commerce",
            language=state.get("language", "pt-BR"),
        )

        state["agent_response"] = error_answer
        return state


async def triage_node(state: GraphState) -> GraphState:
    """Triage Agent node.

    Processes query using Triage Agent (out-of-scope query handling).
    Updates state with agent_response.

    Args:
        state: Graph state with query and language.

    Returns:
        Updated state with agent_response.
    """
    try:
        from app.agents.triage import TriageAgent
        from app.infrastructure.llm import get_llm_client

        # Get agent instance
        llm_client = get_llm_client()
        agent = TriageAgent(llm_client)

        # Process state
        updated_state = await agent.process(state)

        logger.info(
            "Triage node completed",
            extra={
                "thread_id": state.get("thread_id"),
                "user_id": state.get("user_id"),
            },
        )

        return updated_state
    except Exception as e:
        logger.error(
            f"Triage node failed: {e}",
            exc_info=True,
            extra={
                "thread_id": state.get("thread_id"),
                "user_id": state.get("user_id"),
            },
        )

        # Create error response
        error_answer = Answer(
            text=f"Erro ao processar query: {str(e)}",
            agent="triage",
            language=state.get("language", "pt-BR"),
        )

        state["agent_response"] = error_answer
        return state

