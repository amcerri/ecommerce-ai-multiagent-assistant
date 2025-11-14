"""
API module (FastAPI application and routes).

Overview
  Provides FastAPI application with CORS, middleware, exception handlers,
  and route registration. Main entry point for the API server.

Design
  - **FastAPI Application**: Main application instance with full configuration.
  - **CORS**: Configurable CORS with origins from settings.
  - **Middleware**: Language detection, rate limiting, and logging.
  - **Exception Handlers**: Comprehensive error handling.

Integration
  - Consumes: Settings, middleware, routes, graph builder, infrastructure.
  - Returns: FastAPI application instance.
  - Used by: Uvicorn server for running the API.
  - Observability: Logs application lifecycle, requests, and errors.

Usage
  >>> from app.api import app
  >>> # Run with: uvicorn app.api.main:app --reload
"""

from app.api.main import app

__all__ = [
    "app",
]

