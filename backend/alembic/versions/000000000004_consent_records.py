"""Add consent_records table (Phase 4).

Additive migration: creates the consent_records table. Append-only event log
for consent grants, denials, and withdrawals per field case and purpose.
Existing tables untouched. No backfill.

Dialect support: SQLite and PostgreSQL.
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "000000000004"
down_revision: Union[str, None] = "000000000003"
branch_labels = None
depends_on = None


_TABLE = "consent_records"


def _table_exists() -> bool:
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
            "migration ran. Manual intervention required."
        )

    try:
        op.create_table(
            _TABLE,
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column(
                "field_case_id",
                sa.Integer(),
                sa.ForeignKey("field_cases.id"),
                nullable=True,
            ),
            sa.Column(
                "subject_user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("purpose", sa.String(length=40), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("policy_version", sa.String(length=100), nullable=True),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(
                "purpose IN ('observation_collection', 'expert_review', "
                "'ai_training', 'precise_location')",
                name="ck_consent_records_purpose",
            ),
            sa.CheckConstraint(
                "status IN ('granted', 'denied', 'withdrawn')",
                name="ck_consent_records_status",
            ),
            sa.CheckConstraint(
                "policy_version IS NULL OR length(trim(policy_version)) > 0",
                name="ck_consent_records_policy_version",
            ),
        )
        op.create_index(
            "ix_consent_records_field_case_id", _TABLE, ["field_case_id"]
        )
        op.create_index("ix_consent_records_id", _TABLE, ["id"])
        op.create_index("ix_consent_records_purpose", _TABLE, ["purpose"])
        op.create_index("ix_consent_records_status", _TABLE, ["status"])
        op.create_index(
            "ix_consent_records_subject_user_id", _TABLE, ["subject_user_id"]
        )
    except Exception:
        try:
            _cleanup_partial_upgrade()
        except Exception as cleanup_error:
            raise RuntimeError(
                "consent_records migration failed and partial DDL could not be "
                "cleaned up; restore the verified backup before retrying"
            ) from cleanup_error
        raise


def downgrade() -> None:
    raise RuntimeError(
        "This revision is non-destructive by design; restore a verified backup "
        "instead of dropping consent audit trail data."
    )