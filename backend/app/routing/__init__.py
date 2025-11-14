"""
Routing module (semantic routing and allowlist validation).

Overview
  Provides semantic routing functionality using embeddings and LLM for agent
  selection, and allowlist validation for SQL queries. CRITICAL: Routing is
  based on semantic understanding, NEVER on keywords.

Design
  - **Semantic Routing**: Uses embeddings + LLM for routing decisions (NO keywords).
  - **LLM Classifier**: Classifies queries semantically based on intent.
  - **Allowlist Validation**: Validates SQL queries against allowed tables/columns.
  - **Caching**: Caches embeddings and routing decisions for performance.

Integration
  - Consumes: LLM client, embeddings, cache, allowlist.json.
  - Returns: Routing decisions and validation results.
  - Used by: Router node in LangGraph, Analytics agent.
  - Observability: Logs routing decisions and validation results.

Usage
  >>> from app.routing import Router, get_router, AllowlistValidator
  >>> router = get_router()
  >>> decision = await router.route("How many orders?", "pt-BR")
  >>> validator = AllowlistValidator()
  >>> validator.validate_sql("SELECT * FROM orders LIMIT 10")
"""

from app.routing.allowlist import AllowlistValidator
from app.routing.classifier import LLMClassifier
from app.routing.router import Router, get_router

__all__ = [
    "Router",
    "get_router",
    "LLMClassifier",
    "AllowlistValidator",
]

