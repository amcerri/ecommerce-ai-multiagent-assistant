"""
Tracing infrastructure module (distributed tracing with OpenTelemetry).

Overview
  Provides distributed tracing infrastructure using OpenTelemetry. Supports
  span creation, context propagation, and automatic instrumentation of
  common libraries (FastAPI, SQLAlchemy, HTTP clients, etc.).

Design
  - **OpenTelemetry**: Standard distributed tracing implementation.
  - **Context Managers**: Easy span creation with context managers.
  - **Automatic Instrumentation**: Instrumentation of common libraries.

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

from app.infrastructure.tracing.tracer import configure_tracing, get_tracer, start_span

__all__ = [
    "configure_tracing",
    "get_tracer",
    "start_span",
]

