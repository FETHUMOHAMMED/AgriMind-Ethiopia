"""Add nullable prediction provenance fields.

This revision is deliberately additive. Existing prediction rows are not
read, hashed, rewritten, or populated; their new provenance fields remain
NULL until a later, explicitly approved application workflow records reliable
evidence.

Failure recovery:
    SQLite DDL is non-transactional in Alembic. To prevent a partial upgrade
    from being mistaken for a successful one, the migration captures the
    schema (columns AND indexes) BEFORE any DDL runs and only cleans up
    objects it actually created. If cleanup itself fails, the caller raises
    an explicit recovery error and the operator must restore the verified
    backup before retrying.
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
    """Snapshot the current column names on the predictions table."""
    connection = op.get_bind()
    return {
        row[1]
        for row in connection.exec_driver_sql(
            'PRAGMA table_info("predictions")'
        ).fetchall()
    }


def _capture_predictions_indexes() -> set[str]:
    """Snapshot the current index names on the predictions table."""
    connection = op.get_bind()
    return {
        row[1]
        for row in connection.exec_driver_sql(
            'PRAGMA index_list("predictions")'
        ).fetchall()
    }


def _cleanup_partial_upgrade(
    pre_columns: set[str],
    pre_indexes: set[str],
) -> None:
    """Remove only schema objects proven to have been created by this migration.

    Args:
        pre_columns: Column set captured BEFORE any DDL in upgrade() ran.
        pre_indexes: Index set captured BEFORE any DDL in upgrade() ran.

    Only columns/indexes present in the CURRENT schema but ABSENT from the
    pre-snapshot are candidates for cleanup. Anything that already existed
    before the migration started is never touched, because dropping it would
    destroy data this migration did not create.
    """
    connection = op.get_bind()
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

    # Snapshot schema BEFORE any DDL. Used for safe cleanup on failure.
    pre_columns = _capture_predictions_columns()
    pre_indexes = _capture_predictions_indexes()

    # Fail-closed if any provenance column already exists BEFORE we start.
    # We cannot safely clean up in that case — we would not know whether the
    # pre-existing object was created by this migration or by manual
    # intervention.
    conflicts = set(_PROVENANCE_COLUMNS) & pre_columns
    if conflicts:
        raise RuntimeError(
            "Cannot safely migrate: provenance columns already exist before "
            f"this migration ran: {sorted(conflicts)}. "
            "Manual intervention required — investigate before retrying."
        )

    # Fail-closed if the provenance index already exists BEFORE we start.
    if _PROVENANCE_INDEX in pre_indexes:
        raise RuntimeError(
            "Cannot safely migrate: provenance index already exists before "
            f"this migration ran: {_PROVENANCE_INDEX}. "
            "Manual intervention required — investigate before retrying."
        )

    try:
        # All columns are nullable because the legacy baseline did not record
        # provenance. SQLite can add these columns without a table rebuild.
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
        # Bare raise preserves the original traceback (better than `raise exc`)
        raise


def downgrade() -> None:
    """Require backup recovery instead of destructively dropping provenance."""

    raise RuntimeError(
        "This revision is non-destructive by design; restore a verified "
        "backup instead of dropping prediction provenance columns."
    )