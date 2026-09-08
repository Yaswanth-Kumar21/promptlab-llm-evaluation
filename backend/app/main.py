"""
PromptLab — FastAPI application entry point.

Startup sequence:
  1. Configure structured logging
  2. Create FastAPI app with metadata (powers Swagger UI)
  3. Register middleware (CORS, request ID, timing)
  4. Register API routers
  5. Initialise database tables on first run
  6. Log startup confirmation

Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health, providers, prompts, experiments, evaluations, documents, rag
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import configure_logging, get_logger

# ── Configure logging before anything else ───────────────────────────────────
configure_logging()
logger = get_logger(__name__)


# ── Lifespan: startup and shutdown logic ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Code here runs once at startup (before the first request) and once at
    shutdown (after the last request is handled).
    """
    logger.info(
        "promptlab_starting",
        version=settings.app_version,
        env=settings.app_env,
        db=settings.database_url.split("///")[0],  # log driver only, not path
    )

    # Create database tables (development convenience)
    # In production: use `alembic upgrade head` instead
    await init_db()
    logger.info("database_ready")

    yield  # Application runs here

    logger.info("promptlab_shutdown")


# ── FastAPI application instance ─────────────────────────────────────────────
app = FastAPI(
    title="PromptLab API",
    description=(
        "**PromptLab** — LLM Prompt Engineering, Evaluation, RAG & AI Safety Platform.\n\n"
        "This API powers all prompt management, evaluation, RAG, and safety features.\n\n"
        "### Getting started\n"
        "1. Copy `.env.example` to `.env` and set at least one LLM provider API key.\n"
        "2. The `mock` provider works without any API key for development.\n"
        "3. Check `GET /api/providers` to see which providers are configured.\n\n"
        "### Security\n"
        "API keys are read from environment variables and **never** returned in responses."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── CORS middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID + timing middleware ────────────────────────────────────────────
@app.middleware("http")
async def request_middleware(request: Request, call_next) -> Response:
    """
    Attach a unique request ID to every request and log latency.

    The request ID is:
      - Added to response headers as X-Request-ID
      - Available in logs for correlation

    SECURITY: This middleware never logs request bodies (which may
    contain prompts or documents with sensitive information).
    """
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    # Make request_id available to route handlers via request.state
    request.state.request_id = request_id

    try:
        response: Response = await call_next(request)
    except Exception as exc:
        # Catch unhandled exceptions so we can log them safely
        # without exposing stack traces to the client
        logger.error(
            "unhandled_exception",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            error=type(exc).__name__,
            # Intentionally NOT logging exc details to avoid leaking internals
        )
        error_response = JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again.",
                "request_id": request_id,
            },
        )
        error_response.headers["X-Request-ID"] = request_id
        return error_response

    latency_ms = round((time.perf_counter() - start) * 1000)

    logger.info(
        "request_completed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=latency_ms,
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Latency-Ms"] = str(latency_ms)
    return response


# ── API routers ───────────────────────────────────────────────────────────────
# All routes live under /api/ for clear separation from any future static files

app.include_router(health.router, prefix="/api")
app.include_router(providers.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(rag.router, prefix="/api")


# ── Root redirect ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Redirect hint for anyone hitting the bare root URL."""
    return {
        "message": "PromptLab API is running.",
        "docs": "/docs",
        "health": "/api/health",
        "version": settings.app_version,
    }
