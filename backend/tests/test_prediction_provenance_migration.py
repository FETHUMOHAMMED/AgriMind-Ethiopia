"""Disposable-database tests for revision 000000000002."""

from __future__ import annotations

import hashlib
import importlib.metadata
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest


PROVENANCE_COLUMNS = {
    "image_sha256": ("VARCHAR(64)", 0),
    "image_processing_history": ("VARCHAR(2000)", 0),
    "model_version": ("VARCHAR(100)", 0),
    "inference_timestamp": ("DATETIME", 0),
}


@pytest.fixture
def disposable_database_dir():
    with tempfile.TemporaryDirectory(
        prefix="agrimind_provenance_migration_",
        ignore_cleanup_errors=True,
    ) as directory:
        yield Path(directory)


def _create_legacy_fixture(
    path: Path,
    *,
    confidence_type: str = "FLOAT",
    include_unexpected_table: bool = False,
) -> None:
    """Create the committed 000000000001 schema without importing models."""

    with sqlite3.connect(path) as connection:
        connection.executescript(
            f"""
            PRAGMA foreign_keys=ON;
            CREATE TABLE users (
                id INTEGER NOT NULL PRIMARY KEY,
                full_name VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                phone VARCHAR,
                password_hash VARCHAR NOT NULL,
                language VARCHAR,
                role VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX ix_users_email ON users (email);
            CREATE INDEX ix_users_id ON users (id);
            CREATE TABLE predictions (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                image_url VARCHAR,
                disease VARCHAR NOT NULL,
                confidence {confidence_type},
                recommendation VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            CREATE INDEX ix_predictions_id ON predictions (id);
            CREATE TABLE feedbacks (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                prediction_id INTEGER NOT NULL,
                correct BOOLEAN NOT NULL,
                comment VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(prediction_id) REFERENCES predictions(id)
            );
            CREATE INDEX ix_feedbacks_id ON feedbacks (id);
            {"CREATE TABLE unexpected_table (id INTEGER PRIMARY KEY);" if include_unexpected_table else ""}
            """
        )


def _populate_legacy_fixture(path: Path) -> None:
    _create_legacy_fixture(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO users
                (id, full_name, email, phone, password_hash, language, role, created_at)
            VALUES
                (1, 'Legacy Farmer', 'legacy@example.com', '+251900000000',
                 'legacy-hash', 'en', 'farmer', '2024-01-02 03:04:05')
            """
        )
        connection.execute(
            """
            INSERT INTO predictions
                (id, user_id, image_url, disease, confidence, recommendation, created_at)
            VALUES
                (10, 1, 'uploads/predictions/legacy.png', 'wheat rust', 0.875,
                 'inspect crop', '2024-01-03 04:05:06')
            """
        )
        connection.execute(
            """
            INSERT INTO feedbacks
                (id, user_id, prediction_id, correct, comment, created_at)
            VALUES
                (100, 1, 10, 1, 'legacy feedback', '2024-01-04 05:06:07')
            """
        )


def _alembic_command():
    try:
        importlib.metadata.version("alembic")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("Alembic is declared but not installed in this test environment")

    repository_root = str(Path(__file__).parents[1].resolve())
    original_path = list(sys.path)
    sys.path = [
        entry for entry in sys.path
        if Path(entry or ".").resolve() != Path(repository_root)
    ]
    sys.modules.pop("alembic", None)
    try:
        from alembic import command
    finally:
        sys.path = original_path
    return command


def _alembic_config(database: Path, command_function, *x_arguments: str):
    from alembic.config import Config

    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(
        x=[f"db_url=sqlite:///{database.as_posix()}", *x_arguments],
        cmd=(command_function, (), {}),
    )
    return config


def _stamp_baseline(database: Path) -> None:
    command = _alembic_command()
    config = _alembic_config(
        database,
        command.stamp,
        "allow_existing=true",
        "baseline_preflight=verified",
    )
    command.stamp(config, "000000000001")


def _upgrade_head(database: Path) -> None:
    command = _alembic_command()
    config = _alembic_config(database, command.upgrade, "allow_existing=true")
    command.upgrade(config, "head")


def _revision_and_columns(database: Path) -> tuple[list[str], dict[str, tuple[str, int]]]:
    with sqlite3.connect(database) as connection:
        revisions = [
            row[0]
            for row in connection.execute(
                "SELECT version_num FROM alembic_version ORDER BY version_num"
            )
        ]
        columns = {
            row[1]: (row[2].upper(), row[3])
            for row in connection.execute("PRAGMA table_info(predictions)")
        }
    return revisions, columns


def _legacy_values(database: Path) -> dict[str, list[tuple]]:
    with sqlite3.connect(database) as connection:
        return {
            "users": connection.execute(
                "SELECT id, full_name, email, phone, password_hash, language, role, created_at "
                "FROM users ORDER BY id"
            ).fetchall(),
            "predictions": connection.execute(
                "SELECT id, user_id, image_url, disease, confidence, recommendation, created_at "
                "FROM predictions ORDER BY id"
            ).fetchall(),
            "feedbacks": connection.execute(
                "SELECT id, user_id, prediction_id, correct, comment, created_at "
                "FROM feedbacks ORDER BY id"
            ).fetchall(),
        }


def test_fresh_database_reaches_prediction_provenance_revision(
    disposable_database_dir: Path,
):
    database = disposable_database_dir / "fresh-provenance.db"

    _upgrade_head(database)

    revisions, columns = _revision_and_columns(database)
    assert revisions == ["000000000002"]
    assert {name: columns[name] for name in PROVENANCE_COLUMNS} == PROVENANCE_COLUMNS


def test_exact_legacy_data_is_preserved_and_new_fields_remain_null(
    disposable_database_dir: Path,
):
    database = disposable_database_dir / "legacy-provenance.db"
    _populate_legacy_fixture(database)
    before = _legacy_values(database)

    _stamp_baseline(database)
    _upgrade_head(database)

    after = _legacy_values(database)
    assert after == before

    with sqlite3.connect(database) as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("users", "predictions", "feedbacks")
        }
        assert counts == {"users": 1, "predictions": 1, "feedbacks": 1}
        for column in PROVENANCE_COLUMNS:
            assert connection.execute(
                f"SELECT COUNT(*) FROM predictions WHERE {column} IS NOT NULL"
            ).fetchone()[0] == 0

        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        assert integrity == "ok"
        assert foreign_keys == []

        prediction_indexes = {
            row[1]: row
            for row in connection.execute("PRAGMA index_list(predictions)")
        }
        image_index = prediction_indexes["ix_predictions_image_sha256"]
        assert image_index[2] == 0
        assert image_index[4] == 0
        assert [
            row[2]
            for row in connection.execute(
                "PRAGMA index_info(ix_predictions_image_sha256)"
            )
        ] == ["image_sha256"]
        assert "ix_predictions_id" in prediction_indexes

        foreign_key_columns = {
            (row[3], row[2], row[4], row[5].upper(), row[6].upper())
            for row in connection.execute("PRAGMA foreign_key_list(predictions)")
        }
        assert ("user_id", "users", "id", "NO ACTION", "NO ACTION") in foreign_key_columns


def test_provenance_values_can_be_stored_after_upgrade(
    disposable_database_dir: Path,
):
    database = disposable_database_dir / "new-provenance.db"
    _populate_legacy_fixture(database)
    _stamp_baseline(database)
    _upgrade_head(database)

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO predictions
                (id, user_id, image_url, image_sha256, image_processing_history,
                 disease, confidence, recommendation, model_version, inference_timestamp)
            VALUES
                (11, 1, 'uploads/predictions/new.png',
                 'a' || printf('%063d', 0), '{"schema_version":1}',
                 'wheat rust', 0.91, 'inspect crop', 'model-test-v1',
                 '2026-11-02 10:11:12')
            """
        )
        row = connection.execute(
            """
            SELECT image_sha256, image_processing_history, model_version,
                   inference_timestamp
            FROM predictions WHERE id = 11
            """
        ).fetchone()
        assert row == (
            "a" + "0" * 63,
            '{"schema_version":1}',
            "model-test-v1",
            "2026-11-02 10:11:12",
        )


@pytest.mark.parametrize(
    "fixture_kwargs",
    [
        {"confidence_type": "TEXT"},
        {"include_unexpected_table": True},
    ],
)
def test_drifted_legacy_schema_is_refused_before_upgrade(
    disposable_database_dir: Path,
    fixture_kwargs: dict[str, object],
):
    database = disposable_database_dir / "drifted-provenance.db"
    _create_legacy_fixture(database, **fixture_kwargs)
    before = hashlib.sha256(database.read_bytes()).hexdigest()

    command = _alembic_command()
    config = _alembic_config(database, command.upgrade, "allow_existing=true")
    with pytest.raises(RuntimeError, match="did not pass exact"):
        command.upgrade(config, "head")

    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
        ).fetchone() is None


def test_existing_unversioned_legacy_database_cannot_be_upgraded_silently(
    disposable_database_dir: Path,
):
    database = disposable_database_dir / "unversioned-provenance.db"
    _create_legacy_fixture(database)
    before = hashlib.sha256(database.read_bytes()).hexdigest()

    command = _alembic_command()
    config = _alembic_config(database, command.upgrade, "allow_existing=true")
    with pytest.raises(RuntimeError, match="only be stamped"):
        command.upgrade(config, "head")

    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_failed_revision_rolls_back_schema_and_revision_state(
    disposable_database_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    database = disposable_database_dir / "failed-provenance.db"
    _create_legacy_fixture(database)
    _stamp_baseline(database)

    from alembic.operations import Operations

    def fail_index_creation(*args, **kwargs):
        raise RuntimeError("injected provenance index failure")

    monkeypatch.setattr(Operations, "create_index", fail_index_creation)
    command = _alembic_command()
    config = _alembic_config(database, command.upgrade, "allow_existing=true")
    with pytest.raises(RuntimeError, match="injected provenance index failure"):
        command.upgrade(config, "head")

    revisions, columns = _revision_and_columns(database)
    assert revisions == ["000000000001"]
    assert not (set(PROVENANCE_COLUMNS) & set(columns))

def test_migration_refuses_preexisting_provenance_index(
    disposable_database_dir: Path,
):
    """Verify the migration's own guard against a pre-existing index.

    NOTE: Alembic's preflight (env.py) independently rejects drifted schemas
    that contain unexpected indexes, so this scenario is already prevented at
    a higher level. This test verifies the migration's *defense-in-depth*
    guard by invoking upgrade() directly with a MigrationContext, bypassing
    env.py's preflight.

    The failure mode we're testing: someone manually creates
    ix_predictions_image_sha256 before migration runs. The migration's own
    upgrade() must refuse rather than silently try to create a duplicate index
    (which would fail) and then run cleanup (which could drop the pre-existing
    index).
    """
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine

    database = disposable_database_dir / "preexisting-index.db"
    _create_legacy_fixture(database)

    # Simulate a corrupted state: index created manually before migration
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE INDEX ix_predictions_image_sha256 ON predictions (image_url)"
        )

    # Load the migration module directly
    migration_path = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "000000000002_prediction_provenance.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_000000000002_for_guard_test", migration_path
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    # Invoke upgrade() directly via MigrationContext (bypasses env.py preflight)
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    try:
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                with pytest.raises(
                    RuntimeError, match="provenance index already exists"
                ):
                    migration.upgrade()
    finally:
        engine.dispose()

    # Pre-existing index must remain intact (not dropped by cleanup)
    with sqlite3.connect(database) as connection:
        indexes = {
            row[1]
            for row in connection.execute("PRAGMA index_list(predictions)")
        }
    assert "ix_predictions_image_sha256" in indexes

def test_cleanup_failure_raises_recovery_error(
    disposable_database_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """If cleanup itself fails after a migration failure, a clear recovery
    error is raised and the DB stays at the pre-migration revision.

    This test verifies the fail-closed behavior documented in the migration:
    when the DDL cannot be undone, the operator MUST restore a verified
    backup before retrying — the application will not silently continue with
    a partially migrated database.
    """
    database = disposable_database_dir / "cleanup-failure.db"
    _create_legacy_fixture(database)
    _stamp_baseline(database)

    from alembic.operations import Operations
    from sqlalchemy.engine import Connection

    original_exec = Connection.exec_driver_sql

    def fail_index_creation(*args, **kwargs):
        raise RuntimeError("injected provenance index failure")

    def fail_drop_column(self, statement, *args, **kwargs):
        # Allow PRAGMA and DROP INDEX to succeed during cleanup;
        # fail on the first DROP COLUMN attempt.
        if "DROP COLUMN" in str(statement).upper():
            raise RuntimeError("injected cleanup DROP COLUMN failure")
        return original_exec(self, statement, *args, **kwargs)

    monkeypatch.setattr(Operations, "create_index", fail_index_creation)
    monkeypatch.setattr(Connection, "exec_driver_sql", fail_drop_column)

    command = _alembic_command()
    config = _alembic_config(database, command.upgrade, "allow_existing=true")
    with pytest.raises(RuntimeError, match="restore the verified backup"):
        command.upgrade(config, "head")

    # Revision must remain at the pre-migration baseline
    with sqlite3.connect(database) as connection:
        revisions = [
            r[0]
            for r in connection.execute(
                "SELECT version_num FROM alembic_version ORDER BY version_num"
            )
        ]
    assert revisions == ["000000000001"]
