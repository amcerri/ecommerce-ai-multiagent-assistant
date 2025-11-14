"""
Health check API schemas (request/response models for health endpoints).

Overview
  Provides Pydantic models for health check endpoints. Defines response structures
  for health, readiness, and liveness checks used by Kubernetes, Docker, load balancers,
  and monitoring systems.

Design
  - **Response Models**: HealthResponse, ReadinessResponse, LivenessResponse.
  - **Validation**: Automatic validation with Pydantic (Literal types for status values).
  - **Serialization**: Automatic JSON serialization for API responses.

Integration
  - Consumes: None (pure response models).
  - Returns: Validated response models.
  - Used by: Health API routes (Batch 20).
  - Observability: N/A (validation only).

Usage
  >>> from app.api.schemas.health import HealthResponse, ReadinessResponse
  >>> health = HealthResponse(status="ok")
  >>> readiness = ReadinessResponse(status="ready", checks={"database": "ok"})
"""

from typing import Dict, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for basic health check.

    Simple health check response indicating application is running.
    Always returns "ok" if endpoint responds.

    Attributes:
        status: Health status (always "ok" if endpoint responds).

    Validation:
        - status must be "ok"
    """

    status: Literal["ok"] = Field(..., description="Health status (always 'ok' if endpoint responds)")


class ReadinessResponse(BaseModel):
    """Response model for readiness check.

    Readiness check response indicating whether all critical dependencies
    are available and working. Includes individual check results for
    database, cache (optional), and LLM client.

    Attributes:
        status: Overall readiness status ("ready" or "not_ready").
        checks: Individual dependency check results.
            Keys: "database", "cache", "llm"
            Values: "ok", "error", "optional"

    Validation:
        - status must be "ready" or "not_ready"
        - checks must contain expected keys
    """

    status: Literal["ready", "not_ready"] = Field(..., description="Overall readiness status")
    checks: Dict[str, Literal["ok", "error", "optional"]] = Field(
        ...,
        description="Individual dependency check results",
    )


class LivenessResponse(BaseModel):
    """Response model for liveness check.

    Liveness check response indicating application is running and responsive.
    Always returns "alive" if endpoint responds.

    Attributes:
        status: Liveness status (always "alive" if endpoint responds).

    Validation:
        - status must be "alive"
    """

    status: Literal["alive"] = Field(..., description="Liveness status (always 'alive' if endpoint responds)")

