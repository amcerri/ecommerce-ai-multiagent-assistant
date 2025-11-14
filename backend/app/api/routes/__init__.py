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
from app.api.routes.documents import documents_router
from app.api.routes.health import health_router

__all__ = [
    "chat_router",
    "documents_router",
    "health_router",
]

