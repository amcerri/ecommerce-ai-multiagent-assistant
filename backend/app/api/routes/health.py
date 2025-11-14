"""
Health check API routes (health, readiness, and liveness endpoints).

Overview
  Provides endpoints for health checks, readiness checks, and liveness checks.
  Health checks verify application status, readiness checks verify dependencies,
  and liveness checks verify that the application is running.

Design
  - **Health Check**: Basic status check (always ok if endpoint responds).
  - **Readiness Check**: Verifies critical dependencies (database, cache, LLM).
  - **Liveness Check**: Verifies application is running (always alive if endpoint responds).
  - **Fast Checks**: All checks are fast and non-blocking.

Integration
  - Consumes: Database, cache, LLM client, settings.
  - Returns: JSON with status and checks.
  - Used by: Kubernetes, Docker, load balancers, monitoring systems.
  - Observability: Logs check results.

Usage
  >>> GET /api/v1/health
  >>> {"status": "ok"}
  >>> GET /api/v1/health/ready
  >>> {"status": "ready", "checks": {"database": "ok", "cache": "ok", "llm": "ok"}}
  >>> GET /api/v1/health/live
  >>> {"status": "alive"}
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import DBDep
from app.infrastructure.cache.cache_manager import get_cache_manager
from app.infrastructure.llm import get_llm_client

logger = logging.getLogger(__name__)

# Create router
health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check.

    Returns basic status. Always returns "ok" if endpoint responds.

    Returns:
        JSON with status: "ok".
    """
    return {"status": "ok"}


@health_router.get("/ready")
async def readiness_check(
    db: DBDep,
) -> Dict[str, Any]:
    """Readiness check.

    Verifies that all critical dependencies are available and working.
    Checks database, cache (optional), and LLM client.

    Args:
        db: Database session.

    Returns:
        JSON with status and individual check results.
    """
    checks: Dict[str, str] = {}
    all_ready = True

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        checks["database"] = "error"
        all_ready = False

    # Check cache (optional)
    try:
        cache = get_cache_manager()
        if cache:
            # Try to get a test key
            await cache.get("health_check_test", "routing_decisions")
            checks["cache"] = "ok"
        else:
            checks["cache"] = "optional"
    except Exception as e:
        logger.warning(f"Cache check failed (optional): {e}")
        checks["cache"] = "optional"  # Cache is optional, don't fail readiness

    # Check LLM client
    try:
        llm_client = get_llm_client()
        if llm_client:
            checks["llm"] = "ok"
        else:
            checks["llm"] = "error"
            all_ready = False
    except Exception as e:
        logger.error(f"LLM client check failed: {e}")
        checks["llm"] = "error"
        all_ready = False

    status = "ready" if all_ready else "not_ready"

    return {
        "status": status,
        "checks": checks,
    }


@health_router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Liveness check.

    Verifies that the application is running. Always returns "alive" if endpoint responds.

    Returns:
        JSON with status: "alive".
    """
    return {"status": "alive"}

