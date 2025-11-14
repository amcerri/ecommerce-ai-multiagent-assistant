"""
Logging infrastructure module (structured logging configuration).

Overview
  Provides structured logging infrastructure with JSON formatting, context
  injection, and integration with distributed tracing. Main entry points are
  configure_logging() and get_logger().

Design
  - **Structured Logging**: JSON format for easy parsing and analysis.
  - **Context Injection**: Automatic context (thread_id, user_id, agent, trace_id).
  - **Configurable**: Log levels and formats configurable via settings.

Integration
  - Consumes: app.config.settings, OpenTelemetry tracing.
  - Returns: Configured loggers with context.
  - Used by: All application modules for logging.
  - Observability: Provides logging infrastructure itself.

Usage
  >>> from app.infrastructure.logging import get_logger, configure_logging
  >>> configure_logging(level="INFO", format="json")
  >>> logger = get_logger(__name__, thread_id="123", user_id="456")
  >>> logger.info("Processing request", extra={"key": "value"})
"""

from app.infrastructure.logging.logger import configure_logging, get_logger

__all__ = [
    "configure_logging",
    "get_logger",
]

