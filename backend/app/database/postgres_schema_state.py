"""PostgreSQL-specific schema revision validation (read-only)."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine


def read_postgres_revision(engine: Engine) -> list[str]:
    """Read the alembic_version table read-only. Returns [] if absent.

    Mirrors the SQLite implementation in schema_state._read_revision_sqlite:
    returns [] when the alembic_version table does not exist, or [revision]
    when it does. Uses SET TRANSACTION READ ONLY so any accidental write
    would raise rather than silently succeed.
    """
    with engine.connect() as conn:
        conn.exec_driver_sql("SET TRANSACTION READ ONLY")
        exists = conn.execute(text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'alembic_version' AND table_schema = current_schema()"
        )).fetchone()
        if not exists:
            return []
        rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        return [str(row[0]) for row in rows]