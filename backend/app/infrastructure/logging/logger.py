"""
Logger configuration and management (structured logging setup).

Overview
  Provides logger configuration and management with structured logging,
  context injection, and integration with distributed tracing. Supports
  JSON and text formats, configurable log levels, and automatic context
  injection (thread_id, user_id, agent, trace_id).

Design
  - **Structured Logging**: JSON format for production, text for development.
  - **Context Injection**: Automatic context via LoggerAdapter.
  - **Configurable**: Log levels and formats from settings.

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

import logging
import sys
from typing import Any, Dict, Optional

from app.infrastructure.logging.formatter import StructuredFormatter, TextFormatter

# Global flag to track if logging is configured
_logging_configured = False


class ContextLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for automatic context injection.

    Adds context fields (thread_id, user_id, agent, trace_id) to all log
    records automatically. Context can be updated dynamically.
    """

    def __init__(
        self,
        logger: logging.Logger,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize context logger adapter.

        Args:
            logger: Base logger to wrap.
            context: Initial context dictionary.
        """
        super().__init__(logger, context or {})

    def process(
        self,
        msg: str,
        kwargs: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Process log message and add context.

        Adds context fields to extra dictionary for formatter to include.

        Args:
            msg: Log message.
            kwargs: Log keyword arguments.

        Returns:
            Tuple of (message, kwargs) with context added.
        """
        # Get or create extra dictionary
        extra = kwargs.setdefault("extra", {})

        # Add context fields to extra
        if self.extra:
            for key, value in self.extra.items():
                if value is not None:
                    extra[key] = value

        return msg, kwargs

    def update_context(self, **context: Any) -> None:
        """Update context fields.

        Updates context dictionary with new values. Existing values are
        overwritten, new values are added.

        Args:
            **context: Context fields to update.
        """
        if self.extra is None:
            self.extra = {}
        self.extra.update(context)

    def clear_context(self) -> None:
        """Clear all context fields."""
        self.extra = {}


def configure_logging(
    level: str = "INFO",
    format: str = "json",  # noqa: A002
) -> None:
    """Configure global logging.

    Configures root logger with handlers, formatters, and log levels.
    Supports JSON format for production and text format for development.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: Log format ("json" or "text").
    """
    global _logging_configured

    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter based on format
    if format.lower() == "json":
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter()

    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _logging_configured = True


def get_logger(
    name: str,
    **initial_values: Any,
) -> ContextLoggerAdapter:
    """Get logger with context.

    Creates or retrieves logger and wraps it with ContextLoggerAdapter
    for automatic context injection.

    Args:
        name: Logger name (usually __name__).
        **initial_values: Initial context values (thread_id, user_id, agent, etc.).

    Returns:
        ContextLoggerAdapter with initial context.
    """
    # Ensure logging is configured
    if not _logging_configured:
        configure_logging()

    # Get base logger
    logger = logging.getLogger(name)

    # Create context adapter
    adapter = ContextLoggerAdapter(logger, initial_values)

    return adapter

