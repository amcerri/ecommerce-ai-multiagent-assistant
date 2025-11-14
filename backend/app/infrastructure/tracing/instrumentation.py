"""
Automatic instrumentation for common libraries (OpenTelemetry).

Overview
  Provides automatic instrumentation for common libraries using OpenTelemetry
  instrumentation packages. Supports FastAPI, SQLAlchemy, HTTP clients, and
  Redis. Implements graceful degradation if libraries are not available.

Design
  - **Automatic Instrumentation**: Instruments libraries without code changes.
  - **Graceful Degradation**: Continues if instrumentation fails.
  - **Configurable**: Can be enabled/disabled via settings.

Integration
  - Consumes: OpenTelemetry instrumentation packages.
  - Returns: None (side effects: instruments libraries).
  - Used by: Application startup (main.py).
  - Observability: Provides automatic tracing for common operations.

Usage
  >>> from app.infrastructure.tracing.instrumentation import instrument_all
  >>> instrument_all()
"""

import logging

logger = logging.getLogger(__name__)


def instrument_all() -> None:
    """Instrument all supported libraries.

    Automatically instruments FastAPI, SQLAlchemy, HTTP clients, and Redis
    if available. Continues even if some libraries are not available
    (graceful degradation).
    """
    # FastAPI instrumentation
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        # Note: FastAPIInstrumentor.instrument_app() should be called
        # with the app instance, not here. This function just ensures
        # the instrumentation is available.
        logger.info("FastAPI instrumentation available")
    except ImportError:
        logger.debug("FastAPI instrumentation not available")

    # SQLAlchemy instrumentation
    try:
        from opentelemetry.instrumentation.sqlalchemy import (
            SQLAlchemyInstrumentor,
        )

        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumentation enabled")
    except ImportError:
        logger.debug("SQLAlchemy instrumentation not available")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    # HTTP clients instrumentation (httpx, requests)
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
    except ImportError:
        logger.debug("HTTPX instrumentation not available")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPX: {e}")

    try:
        from opentelemetry.instrumentation.requests import (
            RequestsInstrumentor,
        )

        RequestsInstrumentor().instrument()
        logger.info("Requests instrumentation enabled")
    except ImportError:
        logger.debug("Requests instrumentation not available")
    except Exception as e:
        logger.warning(f"Failed to instrument Requests: {e}")

    # Redis instrumentation
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
        logger.info("Redis instrumentation enabled")
    except ImportError:
        logger.debug("Redis instrumentation not available")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")

    logger.info("Automatic instrumentation completed")


def instrument_fastapi(app: Any) -> None:
    """Instrument FastAPI application.

    Instruments FastAPI application with OpenTelemetry. Should be called
    after creating the FastAPI app instance.

    Args:
        app: FastAPI application instance.
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI application instrumented")
    except ImportError:
        logger.debug("FastAPI instrumentation not available")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")

