"""
Health check endpoint.

GET /api/health
  Returns application status, version, environment, and database connectivity.
  Used by:
  - Docker/container health checks
  - Frontend to verify backend is reachable
  - CI/CD pipelines
"""

import time
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

_start_time = time.time()


@router.get(
    "/health",
    summary="Health check",
    description=(
        "Returns the application health status, version, and database connectivity. "
        "Always returns HTTP 200. Check the 'status' field: "
        "'healthy' means everything is OK; 'degraded' means the DB is unreachable."
    ),
    tags=["System"],
)
async def health_check() -> Dict[str, Any]:
    """
    Perform a lightweight health check.

    This endpoint intentionally does NOT use Depends(get_db) so that
    the health check itself never raises a 500 — it always returns 200
    and reports the database status in the response body.

    Returns:
        status: "healthy" or "degraded"
        database: "ok" or "error"
        uptime_seconds: seconds since the process started
        version: application version string
        environment: development | production
    """
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text as sa_text

    db_status = "ok"
    db_error: str | None = None

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(sa_text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        db_error = type(exc).__name__   # class name only — no stack trace to client
        logger.warning("health_check_db_failed", error=str(exc))

    overall = "healthy" if db_status == "ok" else "degraded"
    uptime = round(time.time() - _start_time, 1)

    response: Dict[str, Any] = {
        "status": overall,
        "version": settings.app_version,
        "environment": settings.app_env,
        "uptime_seconds": uptime,
        "database": db_status,
    }
    if db_error:
        response["database_error"] = db_error

    logger.info("health_check", status=overall, uptime=uptime)
    return response
