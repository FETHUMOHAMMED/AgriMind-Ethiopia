import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Dialect-aware database configuration.
# - Dev / test: SQLite default, preserves current behavior for all 91 tests.
# - Production: refuses to boot without DATABASE_URL (no silent fallback).
_ENV = os.getenv("ENVIRONMENT", "development").strip().lower()
_DATABASE_URL_OVERRIDE = os.getenv("DATABASE_URL")

if not _DATABASE_URL_OVERRIDE:
    if _ENV == "production":
        raise RuntimeError(
            "DATABASE_URL must be set when ENVIRONMENT=production; "
            "refusing to fall back to SQLite in a production environment."
        )
    _DATABASE_URL_OVERRIDE = "sqlite:///./agrimind.db"

DATABASE_URL = _DATABASE_URL_OVERRIDE
_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)


if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        """Enforce declared foreign keys when the application uses SQLite."""
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()