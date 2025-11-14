"""
Triage agent module (out-of-scope query handling).

Overview
  Provides handling for queries outside system scope, greetings, and user
  direction. Main entry point is TriageAgent which processes queries and
  generates human-friendly responses with actionable suggestions.

Design
  - **Query Classification**: Identifies different query types.
  - **Response Generation**: Generates appropriate responses for each type.
  - **Actionable Suggestions**: Provides suggestions for user actions.
  - **Base Agent**: TriageAgent inherits from BaseAgent.

Integration
  - Consumes: BaseAgent, LLMClient.
  - Returns: Answer objects with human-friendly responses and suggestions.
  - Used by: LangGraph orchestration layer (fallback agent).
  - Observability: Logs via BaseAgent and handler.

Usage
  >>> from app.agents.triage import TriageAgent
  >>> agent = TriageAgent(llm_client)
  >>> state = await agent.process(state)
"""

from app.agents.triage.agent import TriageAgent
from app.agents.triage.handler import TriageHandler

__all__ = [
    "TriageAgent",
    "TriageHandler",
]

