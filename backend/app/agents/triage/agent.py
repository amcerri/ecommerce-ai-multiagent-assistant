"""
Triage agent (out-of-scope query handler).

Overview
  Main handler for queries outside system scope, greetings, and user direction.
  Provides human-friendly responses when no other agent is appropriate.
  Inherits from BaseAgent for common functionality.

Design
  - **Query Handling**: Identifies and handles different query types.
  - **Human-Friendly Responses**: Generates helpful, friendly responses.
  - **Actionable Suggestions**: Provides suggestions for user actions.
  - **Base Agent**: Inherits from BaseAgent for common functionality.

Integration
  - Consumes: BaseAgent, TriageHandler, LLMClient.
  - Returns: Updated GraphState with Answer containing response and suggestions.
  - Used by: LangGraph orchestration layer (fallback agent).
  - Observability: Logs via BaseAgent._log_processing.

Usage
  >>> from app.agents.triage import TriageAgent
  >>> agent = TriageAgent(llm_client)
  >>> state = await agent.process(state)
"""

import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.triage.handler import TriageHandler
from app.contracts.answer import Answer, PerformanceMetrics
from app.infrastructure.llm.client import LLMClient


class TriageAgent(BaseAgent):
    """Triage Agent for out-of-scope queries.

    Handles queries outside system scope, greetings, and user direction.
    Provides human-friendly responses with actionable suggestions.
    """

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize Triage Agent.

        Creates handler instance for query processing.

        Args:
            llm_client: LLM client for classification and response generation.
        """
        super().__init__(llm_client, name="triage")
        self._handler = TriageHandler(llm_client)

    async def process(self, state: Any) -> Any:
        """Process query and generate answer.

        Implements abstract method from BaseAgent. Handles query and generates
        human-friendly response with suggestions.

        Args:
            state: Graph state with query, language, etc.

        Returns:
            Updated state with agent_response containing Answer.
        """
        # Step 1: Validate state
        self._validate_state(state)

        total_start_time = time.time()

        try:
            # Extract query and language from state
            query = getattr(state, "query", "")
            language = getattr(state, "language", "pt-BR")

            # Step 2: Handle query
            handle_start = time.time()
            handler_result = await self._handler.handle(query, language)
            handle_time = (time.time() - handle_start) * 1000

            response_type = handler_result["response_type"]
            response_text = handler_result["text"]
            suggestions = handler_result["suggestions"]

            # Step 3: Create PerformanceMetrics
            total_time_ms = (time.time() - total_start_time) * 1000
            performance_metrics = PerformanceMetrics(
                total_time_ms=total_time_ms,
                retrieval_time_ms=None,
                generation_time_ms=handle_time,
                tokens_used=None,  # Could be extracted from LLM response
                cost_estimate=None,
            )

            # Step 4: Create Answer
            answer = Answer(
                text=response_text,
                agent="triage",
                language=language,
                performance_metrics=performance_metrics,
            )

            # Add suggestions to answer metadata (if Answer supports it)
            # For now, we'll include suggestions in the text or store in state
            if suggestions:
                suggestions_text = "\n\n💡 **Sugestões:**\n" + "\n".join(f"- {s}" for s in suggestions)
                answer.text = response_text + suggestions_text

            # Step 5: Update state
            if hasattr(state, "agent_response"):
                state.agent_response = answer
            else:
                setattr(state, "agent_response", answer)

            # Store response metadata in state
            if not hasattr(state, "response_type"):
                setattr(state, "response_type", response_type)
            if not hasattr(state, "suggestions"):
                setattr(state, "suggestions", suggestions)

            # Step 6: Log processing
            await self._log_processing(state, answer)

            return state
        except Exception as e:
            # Use BaseAgent error handling
            return await self._handle_error(e, state)

