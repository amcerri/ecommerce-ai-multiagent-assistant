"""
FastAPI main application (API entry point).

Overview
  Main FastAPI application with CORS configuration, exception handlers,
  middleware, and route registration. Handles startup and shutdown events
  for service initialization and cleanup.

Design
  - **CORS**: Configurable CORS with origins from settings.
  - **Exception Handlers**: Comprehensive exception handling for all error types.
  - **Middleware**: Language detection, rate limiting, and logging.
  - **Event Handlers**: Startup and shutdown for service initialization.

Integration
  - Consumes: Settings, middleware, routes, graph builder.
  - Returns: FastAPI application instance.
  - Used by: Uvicorn server for running the API.
  - Observability: Logs application lifecycle and errors.

Usage
  >>> from app.api import app
  >>> # Run with: uvicorn app.api.main:app --reload
"""

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import add_middleware_to_app
from app.config.exceptions import AppBaseException
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# Import routes
from app.api.routes import chat


# Create FastAPI application
app = FastAPI(
    title="E-Commerce AI Multi-Agent Assistant API",
    version="1.0.0",
    description="API for E-Commerce AI Multi-Agent Assistant with Knowledge, Analytics, Commerce, and Triage agents.",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS Configuration
@app.on_event("startup")
async def startup_event() -> None:
    """Startup event handler.

    Initializes services (database, cache, etc.) on application startup.
    """
    try:
        settings = get_settings()
        logger.info("Application starting up...")

        # Initialize database connection pool (lazy loading, so just verify)
        from app.infrastructure.database.connection import get_db_engine

        engine = await get_db_engine()
        logger.info("Database connection pool initialized")

        # Initialize cache (if available)
        from app.infrastructure.cache import get_cache_manager

        cache = get_cache_manager()
        if cache:
            logger.info("Cache manager initialized")
        else:
            logger.warning("Cache manager not available (graceful degradation)")

        # Initialize LLM client (lazy loading, so just verify)
        from app.infrastructure.llm import get_llm_client

        llm_client = get_llm_client()
        logger.info("LLM client initialized")

        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        # Don't raise - allow application to start even if some services fail


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown event handler.

    Closes connections (database, cache, etc.) on application shutdown.
    """
    try:
        logger.info("Application shutting down...")

        # Close database connections
        from app.infrastructure.database.connection import get_db_engine

        engine = await get_db_engine()
        await engine.dispose()
        logger.info("Database connections closed")

        # Close cache connections (if available)
        from app.infrastructure.cache.redis_client import get_redis_client

        redis_client = get_redis_client()
        if redis_client:
            await redis_client.aclose()
            logger.info("Cache connections closed")

        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# CORS Configuration
# Use default origins if settings not available (for import-time)
try:
    settings = get_settings()
    allowed_origins = getattr(settings, "allowed_origins", ["http://localhost:3000", "http://localhost:8000"])
except Exception:
    # Fallback if settings not available at import time
    allowed_origins = ["http://localhost:3000", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add custom middleware
add_middleware_to_app(app)


# Exception Handlers
@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException) -> Response:
    """Handle custom application exceptions.

    Returns structured JSON response with error details.

    Args:
        request: FastAPI request.
        exc: Application exception.

    Returns:
        JSON response with error information.
    """
    logger.error(
        f"Application exception: {exc.message}",
        extra={
            "error_type": type(exc).__name__,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        },
    )

    return Response(
        content=exc.to_dict(),
        status_code=exc.status_code,
        media_type="application/json",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> Response:
    """Handle Pydantic validation errors.

    Returns structured JSON response with validation details.

    Args:
        request: FastAPI request.
        exc: Validation exception.

    Returns:
        JSON response with validation errors.
    """
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )

    return Response(
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
        status_code=422,
        media_type="application/json",
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    """Handle FastAPI HTTP exceptions.

    Returns structured JSON response with error information.

    Args:
        request: FastAPI request.
        exc: HTTP exception.

    Returns:
        JSON response with error information.
    """
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )

    return Response(
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
        },
        status_code=exc.status_code,
        media_type="application/json",
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> Response:
    """Handle unhandled exceptions.

    Returns generic error response without exposing internal details.
    Logs full error for debugging.

    Args:
        request: FastAPI request.
        exc: Exception.

    Returns:
        Generic JSON error response.
    """
    settings = get_settings()
    is_production = settings.environment == "production"

    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
    )

    # Don't expose internal details in production
    error_message = "Internal server error" if is_production else str(exc)

    return Response(
        content={
            "error": "internal_server_error",
            "message": error_message,
        },
        status_code=500,
        media_type="application/json",
    )


# Register routes
from app.api.routes import chat

app.include_router(chat.chat_router, prefix="/api/v1", tags=["chat"])

# Documents and health routes will be created in Batch 20
# For now, create stub routes
from fastapi import APIRouter

stub_documents = APIRouter()

@stub_documents.get("/documents")
async def stub_documents_endpoint() -> Dict[str, str]:
    return {"message": "Document routes will be implemented in Batch 20"}

stub_health = APIRouter()

@stub_health.get("/health")
async def stub_health_endpoint() -> Dict[str, str]:
    return {"status": "ok"}

app.include_router(stub_documents, prefix="/api/v1", tags=["documents"])
app.include_router(stub_health, prefix="/api/v1", tags=["health"])

