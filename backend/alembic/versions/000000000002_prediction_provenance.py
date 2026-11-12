"""Add nullable prediction provenance fields.

This revision is deliberately additive. Existing prediction rows are not
read, hashed, rewritten, or populated; their new provenance fields remain
NULL until a later, explicitly approved application workflow records reliable
evidence.

Dialect support:
- SQLite: original implementation, unchanged.
- PostgreSQL: added in Phase 3. PostgreSQL supports transactional DDL, so a
  failed upgrade automatically rolls back the partial schema change. The
  cleanup routine is a no-op on PostgreSQL because the transaction rollback
  is sufficient and correct.

Failure recovery (SQLite):
    SQLite DDL is non-transactional in Alembic. To prevent a partial upgrade
    from being mistaken for a successful one, the migration captures the
    schema (columns AND indexes) BEFORE any DDL runs and only cleans up
    objects it actually created. If cleanup itself fails, the caller raises
    an explicit recovery error and the operator must restore the verified
    backup before retrying.

Failure recovery (PostgreSQL):
    Alembic runs each migration inside a transaction when the target supports
    transactional DDL (PostgreSQL does). Any exception inside upgrade() causes
    the entire transaction to roll back, undoing all DDL performed by this
    migration. No explicit cleanup is required.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "000000000002"
down_revision: Union[str, None] = "000000000001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_PROVENANCE_COLUMNS = (
    "image_sha256",
    "image_processing_history",
    "model_version",
    "inference_timestamp",
)
_PROVENANCE_INDEX = "ix_predictions_image_sha256"


def _capture_predictions_columns() -> set[str]:
    """Snapshot current column names on predictions. Dialect-aware."""
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        return {
            row[1]
            for row in connection.exec_driver_sql(
                'PRAGMA table_info("predictions")'
            ).fetchall()
        }
    elif connection.dialect.name == "postgresql":
        rows = connection.exec_driver_sql(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'predictions'"
        ).fetchall()
        return {str(row[0]) for row in rows}
    else:
        raise RuntimeError(
            f"Unsupported database dialect: {connection.dialect.name!r}. "
            "This migration supports only SQLite and PostgreSQL."
        )


def _capture_predictions_indexes() -> set[str]:
    """Snapshot current index names on predictions. Dialect-aware."""
    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        return {
            row[1]
            for row in connection.exec_driver_sql(
                'PRAGMA index_list("predictions")'
            ).fetchall()
        }
    elif connection.dialect.name == "postgresql":
        rows = connection.exec_driver_sql(
            "SELECT indexname FROM pg_indexes "
            "WHERE schemaname = current_schema() AND tablename = 'predictions'"
        ).fetchall()
        return {str(row[0]) for row in rows}
    else:
        raise RuntimeError(
            f"Unsupported database dialect: {connection.dialect.name!r}. "
            "This migration supports only SQLite and PostgreSQL."
        )


def _cleanup_partial_upgrade(
    pre_columns: set[str],
    pre_indexes: set[str],
) -> None:
    """Remove only schema objects proven to have been created by this migration.

    SQLite: explicit DROP COLUMN / DROP INDEX required (non-transactional DDL).
    PostgreSQL: no-op — transactional DDL rolls back automatically.
    """
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        return

    if connection.dialect.name != "sqlite":
        raise RuntimeError(
            f"Unsupported database dialect: {connection.dialect.name!r}."
        )

    current_columns = _capture_predictions_columns()
    current_indexes = _capture_predictions_indexes()
    created_columns = current_columns - pre_columns
    created_indexes = current_indexes - pre_indexes

    if _PROVENANCE_INDEX in created_indexes:
        connection.exec_driver_sql(
            f'DROP INDEX IF EXISTS "{_PROVENANCE_INDEX}"'
        )
    for column in reversed(_PROVENANCE_COLUMNS):
        if column in created_columns:
            connection.exec_driver_sql(
                f'ALTER TABLE "predictions" DROP COLUMN "{column}"'
            )


def upgrade() -> None:
    """Add provenance columns without changing existing prediction data."""

    pre_columns = _capture_predictions_columns()
    pre_indexes = _capture_predictions_indexes()

    conflicts = set(_PROVENANCE_COLUMNS) & pre_columns
    if conflicts:
        raise RuntimeError(
            "Cannot safely migrate: provenance columns already exist before "
            f"this migration ran: {sorted(conflicts)}. "
            "Manual intervention required — investigate before retrying."
        )

    if _PROVENANCE_INDEX in pre_indexes:
        raise RuntimeError(
            "Cannot safely migrate: provenance index already exists before "
            f"this migration ran: {_PROVENANCE_INDEX}. "
            "Manual intervention required — investigate before retrying."
        )

    try:
        op.add_column(
            "predictions",
            sa.Column("image_sha256", sa.String(length=64), nullable=True),
        )
        op.add_column(
            "predictions",
            sa.Column(
                "image_processing_history",
                sa.String(length=2000),
                nullable=True,
            ),
        )
        op.add_column(
            "predictions",
            sa.Column("model_version", sa.String(length=100), nullable=True),
        )
        op.add_column(
            "predictions",
            sa.Column(
                "inference_timestamp",
                sa.DateTime(timezone=True),
                nullable=True,
            ),
        )
        op.create_index(
            _PROVENANCE_INDEX,
            "predictions",
            ["image_sha256"],
            unique=False,
        )
    except Exception:
        try:
            _cleanup_partial_upgrade(pre_columns, pre_indexes)
        except Exception as cleanup_error:
            raise RuntimeError(
                "Prediction provenance migration failed and its partial DDL "
                "could not be cleaned up; restore the verified backup before "
                "retrying"
            ) from cleanup_error
        raise


def downgrade() -> None:
    """Require backup recovery instead of destructively dropping provenance."""

    raise RuntimeError(
        "This revision is non-destructive by design; restore a verified "
        "backup instead of dropping prediction provenance columns."
    )