"""
Logging formatters (structured JSON and text formatters).

Overview
  Provides custom formatters for structured logging. Supports JSON format
  for production and text format for development. Includes context fields
  (thread_id, user_id, agent, trace_id) automatically.

Design
  - **JSON Formatter**: Structured JSON output for production.
  - **Text Formatter**: Human-readable text output for development.
  - **Context Fields**: Automatic inclusion of context in all logs.

Integration
  - Consumes: logging.Formatter, OpenTelemetry context.
  - Returns: Formatted log records.
  - Used by: Logger configuration.
  - Observability: Formats logs for observability systems.

Usage
  >>> from app.infrastructure.logging.formatter import StructuredFormatter
  >>> formatter = StructuredFormatter()
  >>> handler.setFormatter(formatter)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from opentelemetry import trace
    from opentelemetry.trace import format_trace_id, format_span_id

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None  # type: ignore


class StructuredFormatter(logging.Formatter):
    """Formatter for structured JSON logging.

    Formats log records as JSON with timestamp, level, message, module,
    function, line, and context fields (thread_id, user_id, agent, trace_id).
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON-formatted log string.
        """
        # Get trace context if available
        trace_id = None
        span_id = None
        if OPENTELEMETRY_AVAILABLE:
            try:
                span = trace.get_current_span()
                if span and span.get_span_context().is_valid:
                    span_context = span.get_span_context()
                    trace_id = format_trace_id(span_context.trace_id)
                    span_id = format_span_id(span_context.span_id)
            except Exception:
                # Graceful degradation if tracing fails
                pass

        # Build log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context from record (thread_id, user_id, agent, etc.)
        if hasattr(record, "thread_id") and record.thread_id:
            log_entry["thread_id"] = record.thread_id

        if hasattr(record, "user_id") and record.user_id:
            log_entry["user_id"] = record.user_id

        if hasattr(record, "agent") and record.agent:
            log_entry["agent"] = record.agent

        # Add trace context
        if trace_id:
            log_entry["trace_id"] = trace_id
        if span_id:
            log_entry["span_id"] = span_id

        # Add extra fields from record
        if hasattr(record, "extra") and record.extra:
            log_entry.update(record.extra)
        else:
            # Extract extra fields from record attributes
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in (
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "thread_id",
                    "user_id",
                    "agent",
                ):
                    extra_fields[key] = value

            if extra_fields:
                log_entry["extra"] = extra_fields

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Formatter for human-readable text logging.

    Formats log records as readable text with timestamp, level, message,
    and context fields. Useful for development and debugging.
    """

    def __init__(self) -> None:
        """Initialize text formatter."""
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text.

        Args:
            record: Log record to format.

        Returns:
            Text-formatted log string.
        """
        # Add context to message if present
        context_parts = []

        if hasattr(record, "thread_id") and record.thread_id:
            context_parts.append(f"thread_id={record.thread_id}")

        if hasattr(record, "user_id") and record.user_id:
            context_parts.append(f"user_id={record.user_id}")

        if hasattr(record, "agent") and record.agent:
            context_parts.append(f"agent={record.agent}")

        # Add trace context if available
        if OPENTELEMETRY_AVAILABLE:
            try:
                span = trace.get_current_span()
                if span and span.get_span_context().is_valid:
                    span_context = span.get_span_context()
                    trace_id = format_trace_id(span_context.trace_id)
                    context_parts.append(f"trace_id={trace_id}")
            except Exception:
                pass

        # Add context to message
        if context_parts:
            original_message = record.getMessage()
            context_str = " | ".join(context_parts)
            record.msg = f"{original_message} [{context_str}]"
            record.args = ()

        return super().format(record)

