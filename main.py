# main.py
# ─────────────────────────────────────────────────────────────────────────────
# FastAPI application entry point.
# Handles: app creation, middleware, router registration, startup/shutdown.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from config import get_settings
from database import init_db, verify_db_connection

# ── Router Imports ─────────────────────────────────────────────────────────────
# Imported after app creation to avoid circular imports
from routers import careers, assessments, results

# ── Logging Configuration ─────────────────────────────────────────────────────
# Structured logging setup — consistent format across all modules
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan Handler ───────────────────────────────────────────────────────────
# The modern FastAPI way to handle startup and shutdown logic.
# Replaces the deprecated @app.on_event("startup") / @app.on_event("shutdown")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ───────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)

    # 1. Verify database connectivity
    verify_db_connection()

    # 2. Create all tables (safe to call even if tables already exist)
    init_db()

    # 3. Warn if AI is not configured (non-fatal — AI is optional)
    if not settings.OPENAI_API_KEY:
        logger.warning(
            "⚠️  OPENAI_API_KEY not set. "
            "AI enhancement layer will be DISABLED. "
            "Core assessment functionality is unaffected."
        )
    else:
        logger.info("✅ AI service configured (OpenAI)")

    logger.info(f"🌐 API running — Docs available at: /docs")
    logger.info("=" * 60)

    yield  # Application is running

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("🛑 Skellix API shutting down gracefully.")


# ── Application Factory ────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    # Disable docs in production — for MVP, keep them enabled
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ── CORS Middleware ────────────────────────────────────────────────────────────
# Required so Adam's frontend (running on a different port) can call our API.
# For MVP, we allow all origins. Lock this down before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TODO: Replace with Adam's frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],          # Allow GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],          # Allow all headers including custom ones
)


# ── Router Registration ────────────────────────────────────────────────────────
# All routes are prefixed with /api for clarity and future versioning.
# Tags group routes in the /docs Swagger UI — very helpful for the team.

app.include_router(
    careers.router,
    prefix="/api/careers",
    tags=["Careers"],
)

app.include_router(
    assessments.router,
    prefix="/api/assessments",
    tags=["Assessments"],
)

app.include_router(
    results.router,
    prefix="/api/results",
    tags=["Results"],
)


# ── Root Health Check ─────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Root health check")
def root():
    """
    Simple health check endpoint.
    Returns app info — useful for deployment verification and monitoring.
    Adam can ping this to verify the backend is reachable before making
    any real API calls.
    """
    return JSONResponse(content={
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "ai_enabled": settings.OPENAI_API_KEY is not None,
        "docs": "/docs",
    })


@app.get("/health", tags=["Health"], summary="Detailed health check")
def health_check():
    """
    Detailed health status — can be extended later to check DB, AI, etc.
    """
    from database import engine
    from sqlalchemy import text

    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return JSONResponse(content={
        "status": "healthy" if db_status == "connected" else "degraded",
        "services": {
            "database": db_status,
            "ai": "enabled" if settings.OPENAI_API_KEY else "disabled (fallback active)",
        }
    })
