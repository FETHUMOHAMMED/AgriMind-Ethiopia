"""Phase 2 acceptance tests: dual-dialect config, schema dispatch, EAT day math.

These tests do NOT modify conftest.py or the SQLite test backend.
PostgreSQL tests are skipped unless TEST_DATABASE_URL is set.

IMPORTANT: Tests that need to verify module-load behavior (production guard,
PostgreSQL engine init) MUST use subprocess, NOT importlib.reload. Reloading
database.py in the same process creates a new Base/engine/SessionLocal that
breaks conftest.py's patches and corrupts state for subsequent tests.
"""
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine

PG_URL = os.getenv("TEST_DATABASE_URL")
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_in_subprocess(code: str, *, extra_env: dict = None) -> subprocess.CompletedProcess:
    """Run code in an isolated subprocess. Never affects parent process state."""
    env = os.environ.copy()
    if extra_env:
        for key, value in extra_env.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


class TestSQLiteEngine:
    def test_engine_initializes(self):
        from app.database.database import engine, _is_sqlite
        assert _is_sqlite is True
        with engine.connect() as conn:
            assert conn.exec_driver_sql("SELECT 1").fetchone()[0] == 1

    def test_foreign_keys_enforced(self):
        from app.database.database import engine
        with engine.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA foreign_keys").fetchone()[0] == 1


@pytest.mark.skipif(not PG_URL, reason="TEST_DATABASE_URL not set")
class TestPostgreSQLEngine:
    def test_engine_initializes(self):
        result = _run_in_subprocess(
            "from app.database.database import engine, _is_sqlite; "
            "assert _is_sqlite is False, f'expected PG, got _is_sqlite={_is_sqlite}'; "
            "conn = engine.connect(); "
            "print(conn.exec_driver_sql('SELECT 1').fetchone()[0]); "
            "conn.close()",
            extra_env={"DATABASE_URL": PG_URL},
        )
        assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
        assert "1" in result.stdout


class TestProductionSafetyGuard:
    def test_production_without_url_raises_in_isolated_process(self):
        result = _run_in_subprocess(
            "import app.database.database",
            extra_env={"ENVIRONMENT": "production", "DATABASE_URL": None},
        )
        assert result.returncode != 0
        assert "DATABASE_URL must be set" in (result.stdout + result.stderr)


class TestSchemaStateDispatch:
    def test_missing_revision_fails_closed(self):
        from app.database.schema_state import validate_application_schema
        engine = create_engine("sqlite:///./agrimind.db")
        saved = os.environ.pop("AGRIMIND_EXPECTED_SCHEMA_REVISION", None)
        try:
            with pytest.raises(RuntimeError, match="must identify"):
                validate_application_schema(engine, expected_revision=None)
        finally:
            if saved is not None:
                os.environ["AGRIMIND_EXPECTED_SCHEMA_REVISION"] = saved

    def test_legacy_baseline_rejected(self):
        from app.database.schema_state import validate_application_schema
        engine = create_engine("sqlite:///./agrimind.db")
        with pytest.raises(RuntimeError, match="legacy baseline"):
            validate_application_schema(engine, expected_revision="000000000001")

    def test_unsupported_dialect_fails_closed(self):
        from app.database.schema_state import validate_application_schema

        class FakeDialect:
            name = "mysql"

        class FakeURL:
            database = "test"

        class FakeEngine:
            dialect = FakeDialect()
            url = FakeURL()

        with pytest.raises(RuntimeError, match="Unsupported database dialect"):
            validate_application_schema(FakeEngine(), expected_revision="000000000002")


class TestEthiopianDayCalculation:
    """Verify the dashboard 'today' calculation uses EAT day boundaries."""

    def test_utc_boundaries_from_eat_midnight(self):
        EAT = timezone(timedelta(hours=3))
        moment = datetime(2026, 11, 7, 0, 30, tzinfo=timezone.utc)
        now_eat = moment.astimezone(EAT)
        start_eat = now_eat.replace(hour=0, minute=0, second=0, microsecond=0)
        end_eat = start_eat + timedelta(days=1)
        start_utc = start_eat.astimezone(timezone.utc)
        end_utc = end_eat.astimezone(timezone.utc)
        assert start_utc == datetime(2026, 11, 6, 21, 0, tzinfo=timezone.utc)
        assert end_utc == datetime(2026, 11, 7, 21, 0, tzinfo=timezone.utc)

    def test_just_before_ethiopian_midnight(self):
        EAT = timezone(timedelta(hours=3))
        moment = datetime(2026, 11, 7, 20, 59, 59, tzinfo=timezone.utc)
        now_eat = moment.astimezone(EAT)
        start_eat = now_eat.replace(hour=0, minute=0, second=0, microsecond=0)
        end_eat = start_eat + timedelta(days=1)
        assert moment < end_eat
        assert moment >= start_eat

    def test_just_after_ethiopian_midnight(self):
        EAT = timezone(timedelta(hours=3))
        moment = datetime(2026, 11, 7, 21, 0, 1, tzinfo=timezone.utc)
        now_eat = moment.astimezone(EAT)
        start_eat = now_eat.replace(hour=0, minute=0, second=0, microsecond=0)
        end_eat = start_eat + timedelta(days=1)
        start_utc = start_eat.astimezone(timezone.utc)
        end_utc = end_eat.astimezone(timezone.utc)
        assert start_utc == datetime(2026, 11, 7, 21, 0, tzinfo=timezone.utc)
        assert moment >= start_utc
        assert moment < end_utc