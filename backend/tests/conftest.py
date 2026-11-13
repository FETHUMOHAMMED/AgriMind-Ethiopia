"""Pytest fixtures for AgriMind-Ethiopia backend tests.

Redirects ALL database operations AND all prediction uploads to disposable
locations for the test session. Ensures tests never touch:
  - backend/agrimind.db (the development database)
  - backend/uploads/predictions/ (the real upload directory)
  - any PostgreSQL database other than the explicitly-allowlisted test DB

Backend selection (Phase 6):
  TEST_BACKEND=sqlite    (default) — SQLite temp file, unchanged behavior
  TEST_BACKEND=postgres  — Requires TEST_DATABASE_URL pointing at an
                          allowlisted disposable PostgreSQL DB (default:
                          agrimind_p6_test). Schema is created via
                          `alembic upgrade head` (production migration path),
                          NOT via Base.metadata.create_all.

Fail-closed safety:
  - Only specific DB names are allowlisted (agrimind_p6_test).
  - Production DB (agrimind), Phase 4 evidence (agrimind_p4_test),
    and Phase 4.5 evidence (agrimind_p45_test) are explicitly refused.
  - guard_postgres_target() verifies current_database/current_user/schema
    before any test runs.

Both patches happen at MODULE LOAD TIME, before test modules import app.main.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Tests run in an explicitly controlled non-production environment.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AGRIMIND_TESTING", "1")

# ============================================================
# Backend selection
# ============================================================

_TEST_BACKEND = os.environ.get("TEST_BACKEND", "sqlite").strip().lower()
if _TEST_BACKEND not in {"sqlite", "postgres"}:
    raise RuntimeError(
        f"TEST_BACKEND must be 'sqlite' or 'postgres', got {_TEST_BACKEND!r}"
    )

_ALLOWED_PG_DB_NAMES = frozenset({"agrimind_p6_test"})
_FORBIDDEN_PG_DB_NAMES = frozenset({
    "agrimind",           # production
    "agrimind_p4_test",   # Phase 4 evidence
    "agrimind_p45_test",  # Phase 4.5 evidence
    "postgres", "template0", "template1",
})

# ============================================================
# Patch 1: Database engine + session (mode-specific)
# ============================================================

_temp_db_dir = None
_temp_uploads_dir = Path(tempfile.mkdtemp(prefix="agrimind_uploads_"))
_test_url = None
_pg_url = None
_pg_db_name = None

if _TEST_BACKEND == "sqlite":
    # ----------------------------------------------------------
    # SQLite — unchanged behavior from Phase 2 onward
    # ----------------------------------------------------------
    _temp_db_dir = Path(tempfile.mkdtemp(prefix="agrimind_test_"))
    _temp_db = _temp_db_dir / "test_agrimind.db"
    _test_url = f"sqlite:///{_temp_db.as_posix()}"

    _test_engine = create_engine(
        _test_url, connect_args={"check_same_thread": False}
    )

    @event.listens_for(_test_engine, "connect")
    def _enable_test_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    _test_session = sessionmaker(
        autocommit=False, autoflush=False, bind=_test_engine
    )

elif _TEST_BACKEND == "postgres":
    # ----------------------------------------------------------
    # PostgreSQL — Phase 6
    # ----------------------------------------------------------
    _test_url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not _test_url:
        raise RuntimeError(
            "TEST_BACKEND=postgres requires TEST_DATABASE_URL to be set.\n"
            "Example: postgresql://agrimind_app:PWD@127.0.0.1:5432/agrimind_p6_test"
        )

    # Parse URL for db name — fail-closed on any non-allowlisted target
    _parsed = urlparse(_test_url)
    _pg_db_name = _parsed.path.lstrip("/").split("/")[0] if _parsed.path else ""

    if _pg_db_name in _FORBIDDEN_PG_DB_NAMES:
        raise RuntimeError(
            f"TEST_DATABASE_URL targets PROTECTED database {_pg_db_name!r}. "
            f"Refused. Use one of {sorted(_ALLOWED_PG_DB_NAMES)}."
        )
    if _pg_db_name not in _ALLOWED_PG_DB_NAMES:
        raise RuntimeError(
            f"TEST_DATABASE_URL targets {_pg_db_name!r}, which is not in the "
            f"allowlist {sorted(_ALLOWED_PG_DB_NAMES)}. This is a fail-closed "
            f"safety gate — update the allowlist in conftest.py only if you "
            f"genuinely intend to use a different DB."
        )

    # Verify live identity before proceeding
    from sqlalchemy.engine import make_url
    from app.database.postgres_schema_preflight import (
        PgTargetIdentity,
        guard_postgres_target,
    )

    _pg_url = make_url(_test_url)
    _expected_identity = PgTargetIdentity(
        database=_pg_db_name,
        user=_pg_url.username or "",
        schema="public",
    )
    guard_postgres_target(_pg_url, expected=_expected_identity)

    _test_engine = create_engine(_test_url)
    _test_session = sessionmaker(
        autocommit=False, autoflush=False, bind=_test_engine
    )

else:
    # Unreachable — validated above
    raise RuntimeError(f"Unhandled TEST_BACKEND: {_TEST_BACKEND!r}")

# ============================================================
# CRITICAL PATCH ORDER:
# 1. Patch db_module.SessionLocal BEFORE importing app.main
# 2. Then import app.main — every route's `from ... import SessionLocal`
#    evaluates against the patched value
# ============================================================

import app.database.database as db_module
db_module.engine = _test_engine
db_module.SessionLocal = _test_session
db_module.SQLALCHEMY_DATABASE_URL = _test_url
db_module.DATABASE_URL = _test_url
db_module._is_sqlite = _test_url.startswith("sqlite")

# Patch 2: uploads dir (must come AFTER db patch, BEFORE app.main import)
import app.routes.predict as _predict_module
_predict_module.UPLOAD_DIR = str(_temp_uploads_dir)

# Safe to import app.main now — test mode bypasses schema validation
import app.main  # noqa: F401

# Belt-and-braces: patch every route + dependencies module
# (they all use `from app.database.database import SessionLocal` at import
# time, so the pre-import patch at line above already worked — this loop
# protects against future modules that cache the engine differently)
for _mod_name in (
    "app.routes.auth",
    "app.routes.predict",
    "app.routes.users",
    "app.routes.feedback",
    "app.routes.language",
    "app.routes.field_cases",
    "app.routes.expert_reviews",
    "app.routes.uploads",
    "app.routes.training_eligibility",
    "app.utils.dependencies",          # <-- Phase 6: was missing before
):
    try:
        _mod = __import__(_mod_name, fromlist=["SessionLocal"])
        if hasattr(_mod, "SessionLocal"):
            _mod.SessionLocal = _test_session
    except ImportError:
        pass

# ============================================================
# Session-scoped schema setup + teardown
# ============================================================

def _setup_sqlite_schema() -> None:
    """SQLite: create schema from ORM metadata (existing behavior)."""
    db_module.Base.metadata.create_all(bind=_test_engine)


def _setup_postgres_schema() -> None:
    """PostgreSQL: create schema via Alembic upgrade head.

    Runs as a subprocess. env.py creates its own engine from -x db_url, so
    this process's patched _test_engine is untouched.

    Passes BOTH allow_fresh=true and allow_existing=true so the first run
    (empty DB) and subsequent runs (schema already at head) both succeed.
    """
    backend_dir = Path(__file__).parents[1]
    cmd = [
        sys.executable, "-m", "alembic",
        "-x", f"db_url={_test_url}",
        "-x", f"expected_database={_pg_db_name}",
        "-x", f"expected_user={_pg_url.username}",
        "-x", "expected_schema=public",
        "-x", "allow_fresh=true",
        "-x", "allow_existing=true",
        "upgrade", "head",
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=backend_dir
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed on {_test_url}:\n"
            f"--- STDOUT ---\n{result.stdout}\n"
            f"--- STDERR ---\n{result.stderr}"
        )


def _truncate_postgres_data() -> None:
    """Reset all data tables but keep schema + alembic_version intact.

    Faster than drop/recreate. Preserves the schema for the next test run.
    TRUNCATE ... CASCADE handles FK ordering automatically.
    """
    data_tables = [
        "expert_adjudications",
        "expert_reviews",
        "consent_records",
        "field_cases",
        "feedbacks",
        "predictions",
        "users",
    ]
    with _test_engine.begin() as conn:
        conn.exec_driver_sql(
            f"TRUNCATE TABLE {', '.join(data_tables)} RESTART IDENTITY CASCADE"
        )


@pytest.fixture(scope="session", autouse=True)
def use_temp_environment():
    """Ensure schema exists in test DB, then clean up after session."""
    if _TEST_BACKEND == "sqlite":
        _setup_sqlite_schema()
        yield
    else:
        _setup_postgres_schema()
        yield
        # Data truncation only; schema persists for next run
        try:
            _truncate_postgres_data()
        except Exception as exc:
            print(f"WARN: PG data truncation at teardown failed: {exc}",
                  file=sys.stderr)

    # Common cleanup
    _test_engine.dispose()
    if _temp_db_dir is not None:
        shutil.rmtree(_temp_db_dir, ignore_errors=True)
    shutil.rmtree(_temp_uploads_dir, ignore_errors=True)