"""Pytest fixtures for AgriMind-Ethiopia backend tests.

Redirects ALL database operations AND all prediction uploads to temporary
locations for the test session. Ensures tests never touch:
  - backend/agrimind.db (the development database)
  - backend/uploads/predictions/ (the real upload directory)

Both patches happen at MODULE LOAD TIME, before test modules import app.main.
"""
import shutil
import tempfile
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Tests run in an explicitly controlled non-production environment. This is
# set before importing application modules because JWT configuration is now
# intentionally fail-closed when ENVIRONMENT is absent or unsupported.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AGRIMIND_TESTING", "1")

# ============================================================
# MODULE-LEVEL PATCHES — run before any test module imports
# ============================================================

# --- Patch 1: Database ---
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

import app.database.database as db_module
db_module.engine = _test_engine
db_module.SessionLocal = _test_session
db_module.SQLALCHEMY_DATABASE_URL = _test_url

# --- Patch 2: Prediction upload directory ---
# Must come AFTER db patch but BEFORE app.main import
_temp_uploads_dir = Path(tempfile.mkdtemp(prefix="agrimind_uploads_"))

import app.routes.predict as _predict_module
_predict_module.UPLOAD_DIR = str(_temp_uploads_dir)

# Now safe to import app.main: test mode permits the application to load
# without performing schema initialization, and prediction uploads go to the
# temp directory. The fixture below creates the disposable schema explicitly.
import app.main  # noqa: F401

# Patch every route module that cached SessionLocal at import time
for _mod_name in (
    "app.routes.auth",
    "app.routes.predict",
    "app.routes.users",
    "app.routes.feedback",
    "app.routes.language",
    "app.routes.field_cases",
    "app.routes.expert_reviews",
    "app.routes.uploads",
):
    try:
        _mod = __import__(_mod_name, fromlist=["SessionLocal"])
        if hasattr(_mod, "SessionLocal"):
            _mod.SessionLocal = _test_session
    except ImportError:
        pass


@pytest.fixture(scope="session", autouse=True)
def use_temp_environment():
    """Ensure tables exist in temp DB, then clean up after session."""
    db_module.Base.metadata.create_all(bind=_test_engine)
    yield
    _test_engine.dispose()
    shutil.rmtree(_temp_db_dir, ignore_errors=True)
    shutil.rmtree(_temp_uploads_dir, ignore_errors=True)
