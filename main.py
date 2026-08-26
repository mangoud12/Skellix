# main.py

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from routers import assessment, careers, questions, roadmap, mvp
from routers import auth
from database import init_db, verify_db_connection


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manage application startup and shutdown events.

    Add DB connection pools, cache warm-up, or background workers here.
    """
    # --- Startup ---
    print("[skillix] Starting up...")
    verify_db_connection()
    init_db()

    yield  # Application runs here

    # --- Shutdown ---
    print("[skillix] Shutting down...")
    # e.g. await db.disconnect()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    app = FastAPI(
        title="Skillix API",
        summary="AI-powered skill learning platform — career paths, assessments & roadmaps.",
        description=(
            "## Skillix\n\n"
            "Skillix helps learners discover career paths, assess their current skill level, "
            "and generate personalised week-by-week learning roadmaps.\n\n"
            "### Key Features\n"
            "- **Career Paths** — Browse and search curated career tracks.\n"
            "- **Questions** — Skill-specific assessment questions by topic and difficulty.\n"
            "- **Assessment** — Timed, scored assessment sessions with per-question feedback.\n"
            "- **Roadmap** — AI-generated, pace-aware learning roadmaps with curated resources.\n"
        ),
        version="0.1.0",
        contact={
            "name": "Skillix Engineering",
            "email": "engineering@skillix.io",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # -----------------------------------------------------------------------
    # Middleware
    # -----------------------------------------------------------------------

    # CORS — tighten origins for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Compress large responses automatically
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # -----------------------------------------------------------------------
    # Global exception handlers
    # -----------------------------------------------------------------------

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # In production, log the traceback to Sentry / Datadog here
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal error occurred."},
        )

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------

    app.include_router(careers.router)
    app.include_router(questions.router)
    app.include_router(assessment.router)
    app.include_router(roadmap.router)
    app.include_router(mvp.router)
    app.include_router(auth.router)

    # -----------------------------------------------------------------------
    # Health & meta endpoints
    # -----------------------------------------------------------------------

    @app.get(
        "/",
        tags=["Health"],
        summary="Root",
        include_in_schema=False,
    )
    async def root() -> dict[str, str]:
        return {"service": "skillix-api", "status": "ok", "version": "0.1.0"}

    @app.get(
        "/health",
        tags=["Health"],
        summary="Health check",
        description="Lightweight liveness probe for load balancers and container orchestrators.",
    )
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get(
        "/ping",
        tags=["Health"],
        summary="Ping",
        include_in_schema=False,
    )
    async def ping() -> dict[str, str]:
        return {"ping": "pong"}

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,           # Disable in production
        log_level="info",
    )
