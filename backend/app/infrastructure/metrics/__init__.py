"""
Metrics infrastructure module (Prometheus metrics collection).

Overview
  Provides Prometheus metrics collection infrastructure with standard metrics
  for HTTP, LLM, agents, database, and cache. Supports automatic collection
  via middleware and manual collection via functions.

Design
  - **Prometheus**: Uses prometheus-client library for metrics.
  - **Standard Metrics**: Pre-defined metrics for common operations.
  - **Automatic Collection**: Middleware for automatic HTTP metrics.
  - **Manual Collection**: Functions for custom metrics.

Integration
  - Consumes: prometheus-client, FastAPI.
  - Returns: Metrics collectors and ASGI app for /metrics endpoint.
  - Used by: All application modules for metrics collection.
  - Observability: Provides metrics infrastructure itself.

Usage
  >>> from app.infrastructure.metrics import configure_metrics, inc_counter, asgi_metrics_app
  >>> configure_metrics(service_name="api")
  >>> inc_counter("http_requests_total", labels={"method": "GET", "status_code": "200"})
  >>> metrics_app = asgi_metrics_app()
"""

from app.infrastructure.metrics.collector import (
    asgi_metrics_app,
    configure_metrics,
    get_metrics_content,
    inc_counter,
    metrics_available,
    observe_histogram,
    set_gauge,
)

__all__ = [
    "configure_metrics",
    "inc_counter",
    "set_gauge",
    "observe_histogram",
    "metrics_available",
    "asgi_metrics_app",
    "get_metrics_content",
]

