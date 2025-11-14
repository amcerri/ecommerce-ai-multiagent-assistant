"""
Prometheus metrics collector (metrics collection and management).

Overview
  Provides Prometheus metrics collection with standard metrics for HTTP,
  LLM, agents, database, and cache. Supports counters, gauges, and histograms
  with labels for filtering and aggregation.

Design
  - **Prometheus Client**: Uses prometheus-client library.
  - **Standard Metrics**: Pre-defined metrics for common operations.
  - **Labels**: Labels for filtering and aggregation.
  - **Buckets**: Appropriate buckets for histograms.

Integration
  - Consumes: prometheus-client.
  - Returns: Metrics collectors and ASGI app.
  - Used by: Middleware and application modules.
  - Observability: Provides metrics collection itself.

Usage
  >>> from app.infrastructure.metrics import configure_metrics, inc_counter
  >>> configure_metrics(service_name="api")
  >>> inc_counter("http_requests_total", labels={"method": "GET"})
"""

import logging
from typing import Any, Dict, Optional

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        REGISTRY,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = None  # type: ignore
    Gauge = None  # type: ignore
    Histogram = None  # type: ignore
    REGISTRY = None  # type: ignore
    generate_latest = None  # type: ignore
    CONTENT_TYPE_LATEST = None  # type: ignore

logger = logging.getLogger(__name__)

# Global registry
_registry: Optional[Any] = None
_metrics_configured = False

# Standard metrics
_http_requests_total: Optional[Any] = None
_http_request_duration_seconds: Optional[Any] = None
_llm_requests_total: Optional[Any] = None
_llm_request_duration_seconds: Optional[Any] = None
_llm_tokens_total: Optional[Any] = None
_agent_requests_total: Optional[Any] = None
_agent_request_duration_seconds: Optional[Any] = None
_database_queries_total: Optional[Any] = None
_database_query_duration_seconds: Optional[Any] = None
_cache_hits_total: Optional[Any] = None
_cache_misses_total: Optional[Any] = None

# Custom metrics storage
_custom_counters: Dict[str, Any] = {}
_custom_gauges: Dict[str, Any] = {}
_custom_histograms: Dict[str, Any] = {}


def configure_metrics(service_name: str = "api") -> None:
    """Configure Prometheus metrics.

    Creates registry and initializes standard metrics. Should be called
    once at application startup.

    Args:
        service_name: Service name for metrics labels.
    """
    global _registry, _metrics_configured
    global _http_requests_total, _http_request_duration_seconds
    global _llm_requests_total, _llm_request_duration_seconds, _llm_tokens_total
    global _agent_requests_total, _agent_request_duration_seconds
    global _database_queries_total, _database_query_duration_seconds
    global _cache_hits_total, _cache_misses_total

    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, metrics disabled")
        return

    try:
        # Create registry
        _registry = REGISTRY

        # HTTP metrics
        _http_requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "path", "status_code"],
            registry=_registry,
        )

        _http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "path", "status_code"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=_registry,
        )

        # LLM metrics
        _llm_requests_total = Counter(
            "llm_requests_total",
            "Total number of LLM requests",
            ["model", "operation"],
            registry=_registry,
        )

        _llm_request_duration_seconds = Histogram(
            "llm_request_duration_seconds",
            "LLM request duration in seconds",
            ["model", "operation"],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=_registry,
        )

        _llm_tokens_total = Counter(
            "llm_tokens_total",
            "Total number of LLM tokens",
            ["model", "type"],
            registry=_registry,
        )

        # Agent metrics
        _agent_requests_total = Counter(
            "agent_requests_total",
            "Total number of agent requests",
            ["agent"],
            registry=_registry,
        )

        _agent_request_duration_seconds = Histogram(
            "agent_request_duration_seconds",
            "Agent request duration in seconds",
            ["agent"],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=_registry,
        )

        # Database metrics
        _database_queries_total = Counter(
            "database_queries_total",
            "Total number of database queries",
            ["operation"],
            registry=_registry,
        )

        _database_query_duration_seconds = Histogram(
            "database_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=_registry,
        )

        # Cache metrics
        _cache_hits_total = Counter(
            "cache_hits_total",
            "Total number of cache hits",
            ["cache_type"],
            registry=_registry,
        )

        _cache_misses_total = Counter(
            "cache_misses_total",
            "Total number of cache misses",
            ["cache_type"],
            registry=_registry,
        )

        _metrics_configured = True
        logger.info(f"Metrics configured for service: {service_name}")
    except Exception as e:
        logger.error(f"Failed to configure metrics: {e}", exc_info=True)
        _metrics_configured = False


def metrics_available() -> bool:
    """Check if metrics are available.

    Returns:
        True if metrics are available and configured, False otherwise.
    """
    return PROMETHEUS_AVAILABLE and _metrics_configured


def _get_or_create_counter(name: str, label_names: Optional[list[str]] = None) -> Any:
    """Get or create counter metric.

    Args:
        name: Counter name.
        label_names: Label names list (for creating new counter).

    Returns:
        Counter instance or None if not available.
    """
    if not metrics_available():
        return None

    if name in _custom_counters:
        return _custom_counters[name]

    try:
        counter = Counter(
            name,
            f"Counter: {name}",
            label_names or [],
            registry=_registry,
        )
        _custom_counters[name] = counter
        return counter
    except Exception as e:
        logger.warning(f"Failed to create counter {name}: {e}")
        return None


def _get_or_create_gauge(name: str, label_names: Optional[list[str]] = None) -> Any:
    """Get or create gauge metric.

    Args:
        name: Gauge name.
        label_names: Label names list (for creating new gauge).

    Returns:
        Gauge instance or None if not available.
    """
    if not metrics_available():
        return None

    if name in _custom_gauges:
        return _custom_gauges[name]

    try:
        gauge = Gauge(
            name,
            f"Gauge: {name}",
            label_names or [],
            registry=_registry,
        )
        _custom_gauges[name] = gauge
        return gauge
    except Exception as e:
        logger.warning(f"Failed to create gauge {name}: {e}")
        return None


def _get_or_create_histogram(
    name: str,
    label_names: Optional[list[str]] = None,
    buckets: Optional[list[float]] = None,
) -> Any:
    """Get or create histogram metric.

    Args:
        name: Histogram name.
        label_names: Label names list (for creating new histogram).
        buckets: Histogram buckets (optional).

    Returns:
        Histogram instance or None if not available.
    """
    if not metrics_available():
        return None

    if name in _custom_histograms:
        return _custom_histograms[name]

    try:
        histogram = Histogram(
            name,
            f"Histogram: {name}",
            label_names or [],
            buckets=buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=_registry,
        )
        _custom_histograms[name] = histogram
        return histogram
    except Exception as e:
        logger.warning(f"Failed to create histogram {name}: {e}")
        return None


def inc_counter(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    amount: float = 1.0,
) -> None:
    """Increment counter metric.

    Args:
        name: Counter name.
        labels: Labels dictionary.
        amount: Amount to increment (default: 1.0).
    """
    if not metrics_available():
        return

    try:
        # Check if it's a standard metric
        if name == "http_requests_total" and _http_requests_total:
            if labels:
                _http_requests_total.labels(**labels).inc(amount)
        elif name == "llm_requests_total" and _llm_requests_total:
            if labels:
                _llm_requests_total.labels(**labels).inc(amount)
        elif name == "agent_requests_total" and _agent_requests_total:
            if labels:
                _agent_requests_total.labels(**labels).inc(amount)
        elif name == "database_queries_total" and _database_queries_total:
            if labels:
                _database_queries_total.labels(**labels).inc(amount)
        elif name == "cache_hits_total" and _cache_hits_total:
            if labels:
                _cache_hits_total.labels(**labels).inc(amount)
        elif name == "cache_misses_total" and _cache_misses_total:
            if labels:
                _cache_misses_total.labels(**labels).inc(amount)
        elif name == "llm_tokens_total" and _llm_tokens_total:
            if labels:
                _llm_tokens_total.labels(**labels).inc(amount)
        else:
            # Custom counter
            label_names = list(labels.keys()) if labels else None
            counter = _get_or_create_counter(name, label_names)
            if counter and labels:
                counter.labels(**labels).inc(amount)
            elif counter:
                counter.inc(amount)
    except Exception as e:
        logger.warning(f"Failed to increment counter {name}: {e}")


def set_gauge(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """Set gauge metric.

    Args:
        name: Gauge name.
        value: Gauge value.
        labels: Labels dictionary.
    """
    if not metrics_available():
        return

    try:
        label_names = list(labels.keys()) if labels else None
        gauge = _get_or_create_gauge(name, label_names)
        if gauge and labels:
            gauge.labels(**labels).set(value)
        elif gauge:
            gauge.set(value)
    except Exception as e:
        logger.warning(f"Failed to set gauge {name}: {e}")


def observe_histogram(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None,
) -> None:
    """Observe histogram metric.

    Args:
        name: Histogram name.
        value: Value to observe.
        labels: Labels dictionary.
    """
    if not metrics_available():
        return

    try:
        # Check if it's a standard metric
        if name == "http_request_duration_seconds" and _http_request_duration_seconds:
            if labels:
                _http_request_duration_seconds.labels(**labels).observe(value)
        elif name == "llm_request_duration_seconds" and _llm_request_duration_seconds:
            if labels:
                _llm_request_duration_seconds.labels(**labels).observe(value)
        elif name == "agent_request_duration_seconds" and _agent_request_duration_seconds:
            if labels:
                _agent_request_duration_seconds.labels(**labels).observe(value)
        elif name == "database_query_duration_seconds" and _database_query_duration_seconds:
            if labels:
                _database_query_duration_seconds.labels(**labels).observe(value)
        else:
            # Custom histogram
            label_names = list(labels.keys()) if labels else None
            histogram = _get_or_create_histogram(name, label_names)
            if histogram and labels:
                histogram.labels(**labels).observe(value)
            elif histogram:
                histogram.observe(value)
    except Exception as e:
        logger.warning(f"Failed to observe histogram {name}: {e}")


def get_metrics_content() -> str:
    """Get Prometheus metrics content.

    Generates Prometheus metrics in text format.

    Returns:
        Metrics content as string.
    """
    if not metrics_available():
        return ""

    try:
        return generate_latest(_registry).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}", exc_info=True)
        return ""


def asgi_metrics_app() -> Optional[Any]:
    """Get ASGI app for /metrics endpoint.

    Returns a callable that can be used as a FastAPI route handler.
    This function is kept for backward compatibility but the recommended
    approach is to use get_metrics_content() directly in a FastAPI route.

    Returns:
        Callable for metrics endpoint or None if metrics not available.
    """
    if not metrics_available():
        return None

    async def metrics_endpoint() -> Any:
        """Metrics endpoint handler.

        Returns Prometheus metrics in text format.

        Returns:
            Response with metrics in text/plain format.
        """
        from fastapi import Response

        try:
            content = get_metrics_content()
            return Response(content=content, media_type=CONTENT_TYPE_LATEST)
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}", exc_info=True)
            return Response(content="Error generating metrics", status_code=500)

    return metrics_endpoint

