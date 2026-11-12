"""Add field_cases table (Phase 4).

Additive migration: creates the field_cases table without modifying existing
tables. Existing users, predictions, and feedbacks data is untouched. No
backfill is performed — field_cases starts empty until the application writes
records through the field-case route.

Dialect support: SQLite and PostgreSQL.
- PostgreSQL: transactional DDL; failure auto-rolls back.
- SQLite: non-transactional DDL; partial-upgrade cleanup drops the table.
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "000000000003"
down_revision: Union[str, None] = "000000000002"
branch_labels = None
depends_on = None


_TABLE = "field_cases"


def _table_exists() -> bool:
    """Dialect-aware check: does field_cases already exist?"""
    connection = op.get_bind()
    dialect = connection.dialect.name
    if dialect == "sqlite":
        row = connection.exec_driver_sql(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{_TABLE}'"
        ).fetchone()
        return row is not None
    elif dialect == "postgresql":
        row = connection.exec_driver_sql(
            f"SELECT 1 FROM information_schema.tables "
            f"WHERE table_schema = current_schema() AND table_name = '{_TABLE}'"
        ).fetchone()
        return row is not None
    else:
        raise RuntimeError(f"Unsupported database dialect: {dialect!r}")


def _cleanup_partial_upgrade() -> None:
    """Remove only objects created by this migration.

    SQLite: explicit DROP TABLE required (non-transactional DDL).
    PostgreSQL: no-op — transactional DDL rolls back automatically.
    """
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        return
    if connection.dialect.name == "sqlite":
        connection.exec_driver_sql(f'DROP TABLE IF EXISTS "{_TABLE}"')
    else:
        raise RuntimeError(
            f"Unsupported database dialect: {connection.dialect.name!r}"
        )


def upgrade() -> None:
    if _table_exists():
        raise RuntimeError(
            f"Cannot safely migrate: {_TABLE!r} already exists before this "
            "migration ran. Manual intervention required — investigate before retrying."
        )

    try:
        op.create_table(
            _TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("case_id", sa.String(length=40), nullable=False),
            sa.Column(
                "collector_user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column(
                "prediction_id",
                sa.Integer(),
                sa.ForeignKey("predictions.id"),
                nullable=True,
            ),
            sa.Column("crop", sa.String(length=100), nullable=False),
            sa.Column("variety", sa.String(length=100), nullable=True),
            sa.Column("plant_part", sa.String(length=100), nullable=False),
            sa.Column("growth_stage", sa.String(length=100), nullable=False),
            sa.Column("observed_symptoms", sa.String(length=4000), nullable=False),
            sa.Column("region", sa.String(length=100), nullable=True),
            sa.Column("zone", sa.String(length=100), nullable=True),
            sa.Column("woreda", sa.String(length=100), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("collection_date", sa.Date(), nullable=False),
            sa.Column("consent_status", sa.String(length=20), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(
                "consent_status IN ('granted', 'denied')",
                name="ck_field_cases_consent_status",
            ),
            sa.CheckConstraint(
                "latitude IS NULL OR latitude BETWEEN -90 AND 90",
                name="ck_field_cases_latitude",
            ),
            sa.CheckConstraint(
                "longitude IS NULL OR longitude BETWEEN -180 AND 180",
                name="ck_field_cases_longitude",
            ),
        )
        op.create_index(
            "ix_field_cases_case_id", _TABLE, ["case_id"], unique=True
        )
        op.create_index(
            "ix_field_cases_collector_user_id", _TABLE, ["collector_user_id"]
        )
        op.create_index("ix_field_cases_id", _TABLE, ["id"])
        op.create_index(
            "ix_field_cases_prediction_id", _TABLE, ["prediction_id"]
        )
    except Exception:
        try:
            _cleanup_partial_upgrade()
        except Exception as cleanup_error:
            raise RuntimeError(
                "field_cases migration failed and partial DDL could not be "
                "cleaned up; restore the verified backup before retrying"
            ) from cleanup_error
        raise


def downgrade() -> None:
    raise RuntimeError(
        "This revision is non-destructive by design; restore a verified backup "
        "instead of dropping field observation data."
    )