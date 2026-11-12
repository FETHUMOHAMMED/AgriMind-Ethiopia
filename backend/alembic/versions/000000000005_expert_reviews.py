"""Add expert_reviews table (Phase 4).

Additive migration: creates the expert_reviews table. Per-reviewer immutable
review records. UNIQUE constraint on (field_case_id, reviewer_user_id)
prevents ballot stuffing (one reviewer, one review per case). Existing tables
untouched. No backfill.

Downgrade behavior: deliberately non-destructive. dropping this table would
destroy expert opinion data that cannot be reconstructed from any other source.
Recovery path is restore-from-verified-backup.

Dialect support: SQLite and PostgreSQL.
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "000000000005"
down_revision: Union[str, None] = "000000000004"
branch_labels = None
depends_on = None


_TABLE = "expert_reviews"


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
                nullable=False,
            ),
            sa.Column(
                "reviewer_user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("verified_diagnosis", sa.String(length=200), nullable=True),
            sa.Column("verification_method", sa.String(length=200), nullable=True),
            sa.Column("review_notes", sa.String(length=4000), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "field_case_id",
                "reviewer_user_id",
                name="uq_expert_reviews_case_reviewer",
            ),
            sa.CheckConstraint(
                "status IN ('pending', 'verified', 'uncertain', 'rejected')",
                name="ck_expert_reviews_status",
            ),
            sa.CheckConstraint(
                "status <> 'verified' OR ("
                "verified_diagnosis IS NOT NULL AND length(trim(verified_diagnosis)) > 0 AND "
                "verification_method IS NOT NULL AND length(trim(verification_method)) > 0"
                ")",
                name="ck_expert_reviews_verified_fields",
            ),
            sa.CheckConstraint(
                "status NOT IN ('uncertain', 'rejected') OR "
                "(verification_method IS NOT NULL AND length(trim(verification_method)) > 0)",
                name="ck_expert_reviews_completed_method",
            ),
        )
        op.create_index(
            "ix_expert_reviews_field_case_id", _TABLE, ["field_case_id"]
        )
        op.create_index("ix_expert_reviews_id", _TABLE, ["id"])
        op.create_index(
            "ix_expert_reviews_reviewer_user_id", _TABLE, ["reviewer_user_id"]
        )
        op.create_index(
            "ix_expert_reviews_status", _TABLE, ["status"]
        )
    except Exception:
        try:
            _cleanup_partial_upgrade()
        except Exception as cleanup_error:
            raise RuntimeError(
                "expert_reviews migration failed and partial DDL could not be "
                "cleaned up; restore the verified backup before retrying"
            ) from cleanup_error
        raise


def downgrade() -> None:
    raise RuntimeError(
        "This revision is non-destructive by design; restore a verified backup "
        "instead of dropping expert review data."
    )