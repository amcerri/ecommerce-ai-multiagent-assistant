"""
Metrics middleware (automatic HTTP metrics collection).

Overview
  Provides FastAPI middleware for automatic HTTP metrics collection.
  Collects request count and duration metrics for all HTTP requests.

Design
  - **Automatic Collection**: Collects metrics for all requests automatically.
  - **Standard Metrics**: Uses standard HTTP metrics (http_requests_total,
    http_request_duration_seconds).
  - **Error Handling**: Collects metrics even if request fails.

Integration
  - Consumes: Metrics collector, FastAPI.
  - Returns: None (side effects: collects metrics).
  - Used by: FastAPI application (added in main.py).
  - Observability: Provides automatic metrics collection.

Usage
  >>> from app.infrastructure.metrics.middleware import add_metrics_middleware
  >>> add_metrics_middleware(app)
"""

import logging
import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.infrastructure.metrics.collector import inc_counter, metrics_available, observe_histogram

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic HTTP metrics collection.

    Collects metrics for all HTTP requests including request count and
    duration. Uses standard Prometheus metrics (http_requests_total,
    http_request_duration_seconds).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Process request and collect metrics.

        Collects request count and duration metrics. Continues even if
        metrics collection fails (graceful degradation).

        Args:
            request: FastAPI request.
            call_next: Next middleware/handler.

        Returns:
            Response from next handler.
        """
        if not metrics_available():
            # Skip metrics collection if not available
            return await call_next(request)

        # Get request information
        method = request.method
        path = request.url.path
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            status_code = response.status_code

            # Collect metrics
            try:
                # Normalize path (remove query params, IDs, etc.)
                normalized_path = self._normalize_path(path)

                # Increment request counter
                inc_counter(
                    "http_requests_total",
                    labels={
                        "method": method,
                        "path": normalized_path,
                        "status_code": str(status_code),
                    },
                )

                # Observe request duration
                observe_histogram(
                    "http_request_duration_seconds",
                    duration,
                    labels={
                        "method": method,
                        "path": normalized_path,
                        "status_code": str(status_code),
                    },
                )
            except Exception as e:
                # Don't fail request if metrics collection fails
                logger.warning(f"Failed to collect metrics: {e}")

            return response

        except Exception as e:
            # Calculate duration even if request failed
            duration = time.time() - start_time
            status_code = 500

            # Collect metrics for failed request
            try:
                normalized_path = self._normalize_path(path)

                inc_counter(
                    "http_requests_total",
                    labels={
                        "method": method,
                        "path": normalized_path,
                        "status_code": str(status_code),
                    },
                )

                observe_histogram(
                    "http_request_duration_seconds",
                    duration,
                    labels={
                        "method": method,
                        "path": normalized_path,
                        "status_code": str(status_code),
                    },
                )
            except Exception:
                # Ignore metrics errors
                pass

            # Re-raise exception (will be handled by exception handler)
            raise

    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics.

        Normalizes path by replacing IDs and query parameters with placeholders
        to reduce cardinality of metrics.

        Args:
            path: Request path.

        Returns:
            Normalized path.
        """
        # Remove query parameters
        if "?" in path:
            path = path.split("?")[0]

        # Replace common ID patterns with placeholders
        import re

        # Replace UUIDs
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        return path


def add_metrics_middleware(app: Any) -> None:
    """Add metrics middleware to FastAPI application.

    Adds MetricsMiddleware and /metrics endpoint to the application.
    Only adds if metrics are available.

    Args:
        app: FastAPI application instance.
    """
    if not metrics_available():
        logger.warning("Metrics not available, skipping metrics middleware")
        return

    try:
        # Add metrics middleware
        app.add_middleware(MetricsMiddleware)

        # Add /metrics endpoint
        from app.infrastructure.metrics.collector import get_metrics_content
        from fastapi import Response

        @app.get("/metrics")
        async def metrics_endpoint() -> Response:
            """Prometheus metrics endpoint.

            Returns Prometheus metrics in text format for scraping.

            Returns:
                Response with metrics in text/plain format.
            """
            content = get_metrics_content()
            return Response(content=content, media_type="text/plain; version=0.0.4")

        logger.info("Metrics middleware and /metrics endpoint added")
    except Exception as e:
        logger.error(f"Failed to add metrics middleware: {e}", exc_info=True)

