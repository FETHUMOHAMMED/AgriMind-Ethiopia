"""Add whitespace-rejection CHECK constraints (Phase 4.5).

Ensures observed_symptoms and decision_rationale cannot be whitespace-only,
matching the Pydantic-layer validators added in the same phase.

SQLite: table rebuild via batch_alter_table (SQLite cannot ALTER TABLE
        ADD CONSTRAINT). Alembic's batch mode temporarily disables foreign
        key checks and rebuilds atomically within a transaction.
PostgreSQL: direct ALTER TABLE ADD CONSTRAINT (transactional DDL).

Pre-migration data check (run BEFORE applying to any DB with existing rows):

    SELECT COUNT(*) FROM field_cases
      WHERE length(trim(observed_symptoms)) = 0;
    SELECT COUNT(*) FROM expert_adjudications
      WHERE length(trim(decision_rationale)) = 0;

If either count is > 0, clean up the offending rows first OR use
ADD CONSTRAINT ... NOT VALID and validate after cleanup. Fresh test
databases have zero counts and the constraints apply cleanly.

Dialect support: SQLite (via batch rebuild) and PostgreSQL (direct).
"""

from typing import Union

from alembic import op


revision: str = "000000000007"
down_revision: Union[str, None] = "000000000006"
branch_labels = None
depends_on = None


_CHECKS = (
    (
        "field_cases",
        "ck_field_cases_observed_symptoms_not_blank",
        "length(trim(observed_symptoms)) > 0",
    ),
    (
        "expert_adjudications",
        "ck_expert_adjudications_decision_rationale_not_blank",
        "length(trim(decision_rationale)) > 0",
    ),
)


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    for table, name, condition in _CHECKS:
        if dialect == "sqlite":
            with op.batch_alter_table(table, recreate="always") as batch_op:
                batch_op.create_check_constraint(name, condition)
        elif dialect == "postgresql":
            op.create_check_constraint(name, table, condition)
        else:
            raise RuntimeError(
                f"Unsupported database dialect: {dialect!r}"
            )


def downgrade() -> None:
    raise RuntimeError(
        "This revision is non-destructive by design; restore a verified "
        "backup instead of dropping constraints that protect data integrity."
    )
