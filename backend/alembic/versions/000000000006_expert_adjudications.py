"""Add expert_adjudications table (Phase 4).

Additive migration: creates the expert_adjudications table. One final
adjudication per field case. Existing tables untouched. No backfill.

Unique enforcement: field_case_id uses unique=True, index=True in the ORM
(renders as UNIQUE INDEX, not table-level UNIQUE CONSTRAINT) — enforces
one adjudication per case at the index level.

Dialect support: SQLite and PostgreSQL.
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "000000000006"
down_revision: Union[str, None] = "000000000005"
branch_labels = None
depends_on = None


_TABLE = "expert_adjudications"


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
                "adjudicator_user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("decision", sa.String(length=32), nullable=False),
            sa.Column("final_diagnosis", sa.String(length=200), nullable=True),
            sa.Column("taxonomy_version", sa.String(length=100), nullable=True),
            sa.Column(
                "decision_rationale", sa.String(length=4000), nullable=False
            ),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(
                "decision IN ('agreement', 'disagreement', 'uncertain', 'rejected')",
                name="ck_expert_adjudications_decision",
            ),
            sa.CheckConstraint(
                "decision NOT IN ('agreement', 'disagreement') OR "
                "(final_diagnosis IS NOT NULL AND length(trim(final_diagnosis)) > 0)",
                name="ck_expert_adjudications_final_diagnosis",
            ),
        )
        op.create_index(
            "ix_expert_adjudications_adjudicator_user_id",
            _TABLE,
            ["adjudicator_user_id"],
        )
        op.create_index(
            "ix_expert_adjudications_decision", _TABLE, ["decision"]
        )
        op.create_index(
            "ix_expert_adjudications_field_case_id",
            _TABLE,
            ["field_case_id"],
            unique=True,
        )
        op.create_index("ix_expert_adjudications_id", _TABLE, ["id"])
    except Exception:
        try:
            _cleanup_partial_upgrade()
        except Exception as cleanup_error:
            raise RuntimeError(
                "expert_adjudications migration failed and partial DDL could "
                "not be cleaned up; restore the verified backup before retrying"
            ) from cleanup_error
        raise


def downgrade() -> None:
    raise RuntimeError(
        "This revision is non-destructive by design; restore a verified backup "
        "instead of dropping final adjudication data."
    )