"""
API routes module (FastAPI routers for API endpoints).

Overview
  Provides FastAPI routers for all API endpoints. Includes chat routes (REST and WebSocket),
  document routes, and health check routes. Routes are organized by domain.

Design
  - **Router Organization**: Separate routers for each domain (chat, documents, health).
  - **Prefix and Tags**: Consistent prefix and tags for OpenAPI documentation.
  - **Dependency Injection**: Uses FastAPI Depends for service injection.

Integration
  - Consumes: Dependencies (database, LLM, graph, etc.), schemas, contracts.
  - Returns: HTTP responses and WebSocket messages.
  - Used by: FastAPI application (main.py).
  - Observability: Logs all requests and responses.

Usage
  >>> from app.api.routes import chat_router
  >>> app.include_router(chat_router, prefix="/api/v1")
"""

from app.api.routes.chat import chat_router

# Documents and health routers will be created in Batch 20
# For now, we'll export None to avoid import errors
documents_router = None  # type: ignore
health_router = None  # type: ignore

__all__ = [
    "chat_router",
    "documents_router",
    "health_router",
]

