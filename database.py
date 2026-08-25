# database.py
# ─────────────────────────────────────────────────────────────────────────────
# SQLAlchemy engine, session factory, and Base model definition.
# WAL mode is enabled here at the engine level — applied once on first connect.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine import Engine
from config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


# ── WAL Mode Configuration ────────────────────────────────────────────────────
# SQLite's default journal mode causes write locks that block all readers.
# WAL (Write-Ahead Logging) allows concurrent reads during a write — essential
# for a multi-user demo where several sessions are active simultaneously.
# This listener fires ONCE per new SQLite connection at the driver level.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Applies SQLite performance and reliability PRAGMAs on every new connection.
    These settings are connection-scoped in SQLite, so we set them on connect.
    """
    cursor = dbapi_connection.cursor()

    # Enable WAL mode — concurrent reads + writes without locking
    cursor.execute("PRAGMA journal_mode=WAL")

    # Enforce foreign key constraints (SQLite ignores them by default!)
    # Without this, cascade deletes and FK violations are silently ignored.
    cursor.execute("PRAGMA foreign_keys=ON")

    # Slightly relaxed durability for speed (acceptable for MVP/demo)
    # NORMAL = sync after each WAL checkpoint, not every write
    cursor.execute("PRAGMA synchronous=NORMAL")

    # 64MB shared cache — speeds up read-heavy operations
    cursor.execute("PRAGMA cache_size=-65536")

    cursor.close()
    logger.debug("SQLite PRAGMAs applied: WAL mode, foreign keys ON")


# ── Engine ────────────────────────────────────────────────────────────────────
# check_same_thread=False is required for FastAPI because SQLAlchemy may use
# the same connection across multiple threads (async request handling).
# This is safe because we manage thread safety via the session factory below.
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    # Echoes all SQL to the logger when DEBUG=True — extremely useful for
    # catching unexpected queries during development
    echo=settings.DEBUG,
)


# ── Session Factory ───────────────────────────────────────────────────────────
# autocommit=False  → We control transactions explicitly (commit / rollback)
# autoflush=False   → We control when changes are flushed to DB
# expire_on_commit=False → Keep ORM objects usable after session.commit()
#                          without triggering a second DB query
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Declarative Base ──────────────────────────────────────────────────────────
# All SQLAlchemy models will inherit from this Base.
# DeclarativeBase is the modern (SQLAlchemy 2.0) way — not declarative_base()
class Base(DeclarativeBase):
    pass


# ── Dependency: DB Session ────────────────────────────────────────────────────
def get_db():
    """
    FastAPI dependency that provides a database session per request.
    
    The session is:
      - Created fresh at the start of each request
      - Automatically closed in the finally block (even if an error occurs)
      - Injected into route handlers via FastAPI's Depends() system

    Usage in a route:
        from database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @router.get("/example")
        def example_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Database Initialization ───────────────────────────────────────────────────
def init_db():
    """
    Creates all tables defined in the models if they don't already exist.
    Called once at application startup from main.py.
    
    This is NOT a migration system — for schema changes after initial creation,
    use Alembic. For the MVP, dropping and recreating the DB is acceptable.
    """
    # Import all models here so Base.metadata knows about them before create_all
    # This import order matters — models with FKs must be imported after their
    # referenced models are registered with Base.
    import models.career      # noqa: F401
    import models.skill       # noqa: F401
    import models.question    # noqa: F401
    import models.user        # noqa: F401
    import models.assessment  # noqa: F401
    import models.response    # noqa: F401
    import models.result      # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables initialized successfully.")


def verify_db_connection():
    """
    Health check: verifies the DB is reachable at startup.
    Logs a clear error if the DB file is missing or corrupted.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info(f"✅ Database connected: {settings.DATABASE_URL}")
    except Exception as e:
        logger.critical(f"❌ Database connection failed: {e}")
        raise
