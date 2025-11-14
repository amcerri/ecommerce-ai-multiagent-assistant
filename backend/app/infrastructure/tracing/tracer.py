"""
Tracer configuration and management (OpenTelemetry distributed tracing).

Overview
  Provides OpenTelemetry tracing configuration and management. Supports
  span creation, context propagation, and export to OTLP collectors or
  console. Integrates with logging for trace_id injection.

Design
  - **OpenTelemetry**: Standard distributed tracing implementation.
  - **Context Managers**: Easy span creation with context managers.
  - **Configurable Export**: OTLP exporter or console exporter.

Integration
  - Consumes: app.config.settings, OpenTelemetry SDK.
  - Returns: Tracers and spans for distributed tracing.
  - Used by: All application modules for tracing.
  - Observability: Provides tracing infrastructure itself.

Usage
  >>> from app.infrastructure.tracing import get_tracer, start_span, configure_tracing
  >>> configure_tracing(service_name="api", endpoint="http://localhost:4318")
  >>> tracer = get_tracer(__name__)
  >>> with start_span("operation", attributes={"key": "value"}):
  ...     # Your code here
  ...     pass
"""

import contextlib
from typing import Any, Dict, Optional

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk import resources
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.trace import Status, StatusCode, Tracer

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None  # type: ignore
    Tracer = None  # type: ignore
    Status = None  # type: ignore
    StatusCode = None  # type: ignore

# Global flag to track if tracing is configured
_tracing_configured = False


def configure_tracing(
    service_name: str,
    endpoint: Optional[str] = None,
    service_version: str = "0.1.0",
) -> None:
    """Configure OpenTelemetry tracing.

    Configures OpenTelemetry SDK with resource, exporter, and processor.
    If endpoint is provided, uses OTLP exporter. Otherwise, uses console exporter.

    Args:
        service_name: Service name for resource.
        endpoint: OTLP endpoint URL (optional, uses console if not provided).
        service_version: Service version for resource.
    """
    global _tracing_configured

    if not OPENTELEMETRY_AVAILABLE:
        # Graceful degradation if OpenTelemetry is not available
        return

    try:
        # Create resource
        resource = resources.Resource.create(
            {
                resources.SERVICE_NAME: service_name,
                resources.SERVICE_VERSION: service_version,
            },
        )

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Create exporter
        if endpoint:
            exporter = OTLPSpanExporter(endpoint=endpoint)
        else:
            exporter = ConsoleSpanExporter()

        # Create processor
        processor = BatchSpanProcessor(exporter)

        # Add processor to tracer provider
        tracer_provider.add_span_processor(processor)

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)

        _tracing_configured = True
    except Exception:
        # Graceful degradation if configuration fails
        pass


def get_tracer(name: str) -> Any:
    """Get tracer for module.

    Gets or creates tracer for a module. Returns a no-op tracer if
    OpenTelemetry is not available or tracing is not configured.

    Args:
        name: Tracer name (usually __name__).

    Returns:
        Tracer instance.
    """
    if not OPENTELEMETRY_AVAILABLE or not _tracing_configured:
        # Return no-op tracer if OpenTelemetry is not available
        return NoOpTracer()

    try:
        tracer_provider = trace.get_tracer_provider()
        return tracer_provider.get_tracer(name)
    except Exception:
        # Return no-op tracer if getting tracer fails
        return NoOpTracer()


@contextlib.contextmanager
def start_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    tracer: Optional[Any] = None,
):
    """Start tracing span with context manager.

    Creates a span with the given name and attributes. Automatically
    ends the span when exiting the context manager.

    Args:
        name: Span name.
        attributes: Span attributes (optional).
        tracer: Tracer to use (optional, uses default if not provided).

    Yields:
        Span instance.
    """
    if not OPENTELEMETRY_AVAILABLE or not _tracing_configured:
        # Return no-op context manager if tracing is not available
        with NoOpSpan() as span:
            yield span
        return

    try:
        # Get tracer
        if tracer is None:
            tracer = get_tracer(__name__)

        # Start span (start_as_current_span returns a context manager)
        with tracer.start_as_current_span(name) as span:
            # Set attributes if provided
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            try:
                yield span
            except Exception as e:
                # Mark span as error
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    except Exception:
        # Graceful degradation if span creation fails
        with NoOpSpan() as span:
            yield span


class NoOpTracer:
    """No-op tracer for graceful degradation.

    Provides a tracer interface that does nothing. Used when OpenTelemetry
    is not available or tracing is not configured.
    """

    def start_as_current_span(self, name: str, **kwargs: Any) -> Any:
        """Start no-op span.

        Args:
            name: Span name (ignored).
            **kwargs: Additional arguments (ignored).

        Returns:
            NoOpSpan instance.
        """
        return NoOpSpan()


class NoOpSpan:
    """No-op span for graceful degradation.

    Provides a span interface that does nothing. Used when OpenTelemetry
    is not available or tracing is not configured.
    """

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span attribute (no-op).

        Args:
            key: Attribute key (ignored).
            value: Attribute value (ignored).
        """
        pass

    def set_status(self, status: Any) -> None:
        """Set span status (no-op).

        Args:
            status: Span status (ignored).
        """
        pass

    def record_exception(self, exception: Exception) -> None:
        """Record exception (no-op).

        Args:
            exception: Exception to record (ignored).
        """
        pass

    def end(self) -> None:
        """End span (no-op)."""
        pass

    def __enter__(self) -> "NoOpSpan":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        pass

