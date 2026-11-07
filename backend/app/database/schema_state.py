"""Fail-closed application schema revision validation."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from sqlalchemy.engine import Engine

from app.database.schema_preflight import LEGACY_BASELINE_REVISION


EXPECTED_SCHEMA_REVISION_ENV = "AGRIMIND_EXPECTED_SCHEMA_REVISION"


def _sqlite_path(engine: Engine) -> Path:
    if engine.dialect.name != "sqlite" or not engine.url.database:
        raise RuntimeError(
            "SQLite schema validation requires an on-disk database path"
        )
    path = Path(engine.url.database)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _read_revision_sqlite(path: Path) -> list[str]:
    if not path.exists():
        raise RuntimeError(
            "The application database does not exist; initialize it through an explicit migration command"
        )
    try:
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise RuntimeError("The application database could not be opened read-only") from exc
    try:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
        ).fetchone()
        if not exists:
            return []
        return [str(row[0]) for row in connection.execute("SELECT version_num FROM alembic_version")]
    finally:
        connection.close()


def validate_application_schema(engine: Engine, expected_revision: str | None = None) -> None:
    """Require an explicitly configured, non-foundation migration revision.

    Fail-closed for every dialect. The legacy baseline revision is never
    accepted as sufficient application state.
    """
    expected = expected_revision or os.getenv(EXPECTED_SCHEMA_REVISION_ENV, "").strip()
    if not expected:
        raise RuntimeError(
            f"{EXPECTED_SCHEMA_REVISION_ENV} must identify the completed application schema revision"
        )
    if expected == LEGACY_BASELINE_REVISION:
        raise RuntimeError(
            "The legacy baseline is not sufficient for the current Phase 1-4 application; "
            "apply the approved application upgrade revisions first"
        )

    dialect = engine.dialect.name
    if dialect == "sqlite":
        actual = _read_revision_sqlite(_sqlite_path(engine))
    elif dialect == "postgresql":
        from app.database.postgres_schema_state import read_postgres_revision
        actual = read_postgres_revision(engine)
    else:
        raise RuntimeError(
            f"Unsupported database dialect for schema validation: {dialect}"
        )

    if actual != [expected]:
        raise RuntimeError(
            "The database schema revision does not match the configured application revision"
        )