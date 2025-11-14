"""
API middleware (language detection, rate limiting, logging).

Overview
  Provides FastAPI middleware for language detection, rate limiting, and
  structured logging. All middleware implements graceful degradation if
  optional services are unavailable.

Design
  - **BaseHTTPMiddleware**: All middleware inherits from BaseHTTPMiddleware.
  - **Graceful Degradation**: Continues operation if optional services fail.
  - **Error Handling**: Logs errors but doesn't break request processing.
  - **Structured Logging**: Includes context (IP, user_id, language, etc.).

Integration
  - Consumes: LanguageDetector, CacheManager, Request/Response.
  - Returns: Modified Request/Response with additional state.
  - Used by: FastAPI application (added in main.py).
  - Observability: Logs all middleware operations.

Usage
  >>> from app.api.middleware import add_middleware_to_app
  >>> add_middleware_to_app(app)
"""

import logging
import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.constants import RATE_LIMITS
from app.infrastructure.cache.cache_manager import get_cache_manager
from app.services.language.detector import LanguageDetector

logger = logging.getLogger(__name__)


class LanguageDetectionMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic language detection.

    Detects user language from IP and Accept-Language header and adds
    to request state for use in route handlers.
    """

    def __init__(self, app: Any) -> None:  # type: ignore
        """Initialize language detection middleware.

        Args:
            app: FastAPI application.
        """
        super().__init__(app)
        self._detector = LanguageDetector()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process request and detect language.

        Detects language and adds to request.state.language.

        Args:
            request: FastAPI request.
            call_next: Next middleware/handler.

        Returns:
            Response from next handler.
        """
        try:
            # Get IP address
            ip_address = request.client.host if request.client else None

            # Get Accept-Language header
            accept_language = request.headers.get("Accept-Language")

            # Detect language
            language = await self._detector.detect(ip_address, accept_language)

            # Add to request state
            request.state.language = language

        except Exception as e:
            logger.warning(f"Language detection failed: {e}, using fallback")
            # Graceful degradation: use fallback
            request.state.language = "pt-BR"

        # Continue to next middleware/handler
        response = await call_next(request)
        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for IP-based rate limiting.

    Limits requests per IP address using cache (Redis) for storage.
    Implements graceful degradation if cache is unavailable.
    """

    def __init__(self, app: Any) -> None:  # type: ignore
        """Initialize rate limiting middleware.

        Args:
            app: FastAPI application.
        """
        super().__init__(app)
        self._cache = get_cache_manager()
        # Get rate limits from constants
        per_ip_limits = RATE_LIMITS.get("per_ip", {})
        self._max_requests = per_ip_limits.get("requests", 1000)
        self._window_seconds = per_ip_limits.get("window", 3600)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process request and check rate limit.

        Checks rate limit for IP and returns 429 if exceeded.

        Args:
            request: FastAPI request.
            call_next: Next middleware/handler.

        Returns:
            Response from next handler or 429 if rate limited.
        """
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health") or request.url.path.startswith("/docs"):
            return await call_next(request)

        try:
            # Get IP address
            ip_address = request.client.host if request.client else "unknown"

            if self._cache:
                # Check rate limit in cache
                cache_key = f"rate_limit:{ip_address}"
                current_count = await self._cache.get(cache_key, "routing_decisions")

                if current_count is not None and current_count >= self._max_requests:
                    # Rate limit exceeded
                    logger.warning(
                        f"Rate limit exceeded for IP: {ip_address}",
                        extra={"ip_address": ip_address, "count": current_count},
                    )
                    return Response(
                        content='{"error": "rate_limit_exceeded", "message": "Too many requests"}',
                        status_code=429,
                        media_type="application/json",
                    )

                # Increment counter
                if current_count is None:
                    current_count = 0

                await self._cache.set(
                    cache_key,
                    current_count + 1,
                    "routing_decisions",
                    ttl=self._window_seconds,
                )

        except Exception as e:
            logger.warning(f"Rate limiting failed: {e}, allowing request")
            # Graceful degradation: allow request if rate limiting fails

        # Continue to next middleware/handler
        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging.

    Logs all requests with structured information including method, path,
    IP, status code, and processing time.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process request and log information.

        Logs request start and end with structured information.

        Args:
            request: FastAPI request.
            call_next: Next middleware/handler.

        Returns:
            Response from next handler.
        """
        # Get request information
        method = request.method
        path = request.url.path
        ip_address = request.client.host if request.client else "unknown"
        language = getattr(request.state, "language", "pt-BR")

        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "method": method,
                "path": path,
                "ip_address": ip_address,
                "language": language,
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Log request end
            logger.info(
                f"Request completed: {method} {path} - {response.status_code}",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "processing_time_ms": processing_time_ms,
                    "ip_address": ip_address,
                    "language": language,
                },
            )

            return response

        except Exception as e:
            # Log error
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {method} {path}",
                exc_info=True,
                extra={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "processing_time_ms": processing_time_ms,
                    "ip_address": ip_address,
                    "language": language,
                },
            )
            # Re-raise exception (will be handled by exception handler)
            raise


def add_middleware_to_app(app: Any) -> None:  # type: ignore
    """Add all middleware to FastAPI application.

    Adds language detection, rate limiting, and logging middleware
    to the FastAPI application.

    Args:
        app: FastAPI application instance.
    """
    app.add_middleware(LanguageDetectionMiddleware)
    app.add_middleware(RateLimitingMiddleware)
    app.add_middleware(LoggingMiddleware)

