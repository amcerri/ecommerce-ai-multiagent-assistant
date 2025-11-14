"""
Routing module (semantic routing and allowlist validation).

Overview
  Provides routing functionality including semantic routing decisions and
  allowlist validation for SQL queries. AllowlistValidator will be fully
  implemented in Batch 17.

Design
  - **Semantic Routing**: Uses embeddings and LLM for routing decisions.
  - **Allowlist Validation**: Validates SQL queries against allowed tables/columns.
  - **Extensibility**: Easy to extend with new routing strategies.

Integration
  - Consumes: LLM client, embeddings, database models.
  - Returns: Routing decisions and validation results.
  - Used by: Triage agent, Analytics agent.
  - Observability: Logs routing decisions and validation results.

Usage
  >>> from app.routing.allowlist import AllowlistValidator
  >>> validator = AllowlistValidator()
  >>> is_valid = await validator.validate_sql(sql, tables, columns)
"""

# Allowlist validation
from app.routing.allowlist import AllowlistValidator
from app.routing.router import Router

__all__ = [
    "AllowlistValidator",
    "Router",
]

