"""Disposable-database tests for the migration foundation and preflight."""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import sqlite3
import tempfile
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

from app.database.schema_preflight import (
    DEVELOPMENT_DATABASE,
    SchemaTargetError,
    preflight_database,
)
import app.database.schema_preflight as schema_preflight
from app.database.schema_state import validate_application_schema


@pytest.fixture
def disposable_database_dir():
    with tempfile.TemporaryDirectory(
        prefix="agrimind_migration_test_",
        ignore_cleanup_errors=True,
    ) as directory:
        yield Path(directory)


def _create_legacy_database(path: Path, *, include_role: bool = True) -> None:
    role_column = ", role VARCHAR" if include_role else ""
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
                language VARCHAR{role_column},
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX ix_users_email ON users (email);
            CREATE INDEX ix_users_id ON users (id);
            CREATE TABLE predictions (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                image_url VARCHAR,
                disease VARCHAR NOT NULL,
                confidence FLOAT,
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
            """
        )


def _create_schema_variant(
    path: Path,
    *,
    confidence_type: str = "FLOAT",
    language_not_null: bool = False,
    users_id_primary_key: bool = True,
    created_default: str = "CURRENT_TIMESTAMP",
    check_constraint: str = "",
    cascade_delete: bool = False,
    unique_email: bool = True,
    partial_id_index: bool = False,
    extra_index: bool = False,
    extra_view: bool = False,
    extra_trigger: bool = False,
) -> None:
    users_id = "id INTEGER NOT NULL PRIMARY KEY" if users_id_primary_key else "id INTEGER NOT NULL"
    users_unique_id = "" if users_id_primary_key else ", UNIQUE (id)"
    language = "language VARCHAR NOT NULL" if language_not_null else "language VARCHAR"
    prediction_fk = "FOREIGN KEY(user_id) REFERENCES users(id)"
    if cascade_delete:
        prediction_fk += " ON DELETE CASCADE"
    check_sql = f", {check_constraint}" if check_constraint else ""
    with sqlite3.connect(path) as connection:
        connection.executescript(
            f"""
            PRAGMA foreign_keys=ON;
            CREATE TABLE users (
                {users_id},
                full_name VARCHAR NOT NULL,
                email VARCHAR NOT NULL,
                phone VARCHAR,
                password_hash VARCHAR NOT NULL,
                {language},
                role VARCHAR,
                created_at DATETIME DEFAULT {created_default}{users_unique_id}{check_sql}
            );
            CREATE {'UNIQUE ' if unique_email else ''}INDEX ix_users_email ON users (email);
            CREATE {'INDEX ix_users_id ON users (id) WHERE id > 0' if partial_id_index else 'INDEX ix_users_id ON users (id)'};
            CREATE TABLE predictions (
                id INTEGER NOT NULL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                image_url VARCHAR,
                disease VARCHAR NOT NULL,
                confidence {confidence_type},
                recommendation VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                {prediction_fk}
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
            {"CREATE INDEX unexpected_index ON users (full_name);" if extra_index else ""}
            {"CREATE VIEW unexpected_view AS SELECT id FROM users;" if extra_view else ""}
            {"CREATE TRIGGER unexpected_trigger AFTER INSERT ON users BEGIN SELECT 1; END;" if extra_trigger else ""}
            """
        )


def _alembic_command():
    """Load the installed Alembic package without local-folder shadowing."""

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


def test_preflight_recognizes_unversioned_legacy_baseline(disposable_database_dir: Path):
    database = disposable_database_dir / "legacy.db"
    _create_legacy_database(database)
    before = hashlib.sha256(database.read_bytes()).hexdigest()

    report = preflight_database(database, allow_existing=True)

    assert report["status"] == "recognized_unversioned_legacy_baseline"
    assert report["integrity_check_ok"] is True
    assert report["foreign_key_violation_count"] == 0
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_preflight_reports_missing_columns(disposable_database_dir: Path):
    database = disposable_database_dir / "missing-column.db"
    _create_legacy_database(database, include_role=False)

    report = preflight_database(database, allow_existing=True)

    assert report["status"] == "unknown_or_partial_schema"
    assert "role" in report["missing_columns"]["users"]


def test_preflight_reports_unexpected_tables(disposable_database_dir: Path):
    database = disposable_database_dir / "drift.db"
    _create_legacy_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE unexpected_table (id INTEGER PRIMARY KEY)")

    report = preflight_database(database, allow_existing=True)

    assert report["status"] == "unknown_or_partial_schema"
    assert report["unexpected_tables"] == ["unexpected_table"]


@pytest.mark.parametrize(
    ("name", "options", "expected_key"),
    [
        ("altered-type", {"confidence_type": "TEXT"}, "column_mismatches"),
        ("altered-nullability", {"language_not_null": True}, "column_mismatches"),
        ("altered-primary-key", {"users_id_primary_key": False}, "column_mismatches"),
        ("altered-default", {"created_default": "'2000-01-01'"}, "column_mismatches"),
        (
            "altered-check",
            {"check_constraint": "CHECK (length(full_name) > 0)"},
            "check_constraint_mismatches",
        ),
        ("altered-cascade", {"cascade_delete": True}, "foreign_key_mismatches"),
        ("altered-unique", {"unique_email": False}, "index_mismatches"),
        ("altered-index", {"partial_id_index": True}, "index_mismatches"),
        ("unexpected-index", {"extra_index": True}, "unexpected_indexes"),
        ("unexpected-view", {"extra_view": True}, "unexpected_views"),
        ("unexpected-trigger", {"extra_trigger": True}, "unexpected_triggers"),
    ],
)
def test_preflight_rejects_each_schema_drift(
    disposable_database_dir: Path,
    name: str,
    options: dict[str, object],
    expected_key: str,
):
    database = disposable_database_dir / f"{name}.db"
    _create_schema_variant(database, **options)

    report = preflight_database(database, allow_existing=True)

    assert report["status"] == "unknown_or_partial_schema"
    assert report[expected_key]


def test_preflight_refuses_missing_database_without_creating_it(disposable_database_dir: Path):
    database = disposable_database_dir / "missing.db"

    with pytest.raises(SchemaTargetError, match="does not exist"):
        preflight_database(database)
    assert not database.exists()


@pytest.mark.parametrize("payload", [b"not a sqlite database", b"SQLite format 3\x00invalid"])
def test_preflight_refuses_malformed_sqlite_files(disposable_database_dir: Path, payload: bytes):
    database = disposable_database_dir / "malformed.db"
    database.write_bytes(payload)

    with pytest.raises(SchemaTargetError, match="SQLite schema inspection failed|opened read-only"):
        preflight_database(database, allow_existing=True)


@pytest.mark.skipif(os.name == "nt", reason="Windows ACL behavior is not safely changed in this test")
def test_preflight_refuses_unreadable_file_where_permissions_are_supported(
    disposable_database_dir: Path,
):
    database = disposable_database_dir / "unreadable.db"
    _create_legacy_database(database)
    original_mode = database.stat().st_mode
    database.chmod(0)
    try:
        with pytest.raises(SchemaTargetError):
            preflight_database(database, allow_existing=True)
    finally:
        database.chmod(original_mode)


def test_preflight_refuses_inspection_failure_after_read_only_open(
    disposable_database_dir: Path, monkeypatch: pytest.MonkeyPatch
):
    database = disposable_database_dir / "inspection-failure.db"
    _create_legacy_database(database)

    def fail(*args, **kwargs):
        raise sqlite3.DatabaseError("synthetic inspection failure")

    monkeypatch.setattr(schema_preflight, "_table_info", fail)
    with pytest.raises(SchemaTargetError, match="inspection failed"):
        preflight_database(database, allow_existing=True)


def test_hard_link_to_protected_target_is_refused(disposable_database_dir: Path, monkeypatch):
    protected = disposable_database_dir / "protected.db"
    alias = disposable_database_dir / "alias.db"
    _create_legacy_database(protected)
    try:
        os.link(protected, alias)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")

    monkeypatch.setattr(schema_preflight, "DEVELOPMENT_DATABASE", protected.resolve())
    with pytest.raises(SchemaTargetError, match="aliases the protected"):
        schema_preflight.guard_migration_target(alias, allow_existing=True)


def test_preflight_reports_foreign_key_violations(disposable_database_dir: Path):
    database = disposable_database_dir / "invalid-fk.db"
    _create_legacy_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute(
            "INSERT INTO predictions(id, user_id, disease) VALUES (1, 999, 'unknown')"
        )

    report = preflight_database(database, allow_existing=True)

    assert report["foreign_key_violation_count"] == 1
    assert report["integrity_check_ok"] is True


def test_preflight_requires_explicit_existing_database_acknowledgement(disposable_database_dir: Path):
    database = disposable_database_dir / "existing.db"
    _create_legacy_database(database)

    with pytest.raises(SchemaTargetError, match="allow_existing"):
        preflight_database(database)


def test_preflight_refuses_development_database_without_opening_it():
    with pytest.raises(SchemaTargetError, match="development database"):
        preflight_database(DEVELOPMENT_DATABASE, allow_existing=True)


def test_startup_schema_validation_rejects_missing_or_foundation_state(disposable_database_dir: Path):
    database = disposable_database_dir / "versioned.db"
    _create_legacy_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        connection.execute("INSERT INTO alembic_version(version_num) VALUES ('000000000001')")

    engine = create_engine(f"sqlite:///{database.as_posix()}")
    try:
        with pytest.raises(RuntimeError, match="not sufficient"):
            validate_application_schema(engine, expected_revision="000000000001")
        with pytest.raises(RuntimeError, match="does not match"):
            validate_application_schema(engine, expected_revision="000000000002")
    finally:
        engine.dispose()


def test_fresh_database_initialization_through_alembic(disposable_database_dir: Path):
    command = _alembic_command()
    from alembic.config import Config

    database = disposable_database_dir / "fresh.db"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(
        x=[f"db_url=sqlite:///{database.as_posix()}", "allow_existing=false"]
    )

    command.upgrade(config, "head")
    from alembic.script import ScriptDirectory
    expected_head = ScriptDirectory.from_config(config).get_current_head()
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchall() == [(expected_head,)]
        columns = {
            row[1]: (row[2], row[3])
            for row in connection.execute("PRAGMA table_info(predictions)")
        }
        assert columns["image_sha256"] == ("VARCHAR(64)", 0)
        assert columns["image_processing_history"] == ("VARCHAR(2000)", 0)
        assert columns["model_version"] == ("VARCHAR(100)", 0)
        assert columns["inference_timestamp"] == ("DATETIME", 0)


def test_alembic_refuses_existing_target_without_explicit_acknowledgement(
    disposable_database_dir: Path,
):
    command = _alembic_command()
    from alembic.config import Config

    database = disposable_database_dir / "existing-for-migration.db"
    _create_legacy_database(database)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(
        x=[f"db_url=sqlite:///{database.as_posix()}", "allow_existing=false"]
    )

    with pytest.raises(RuntimeError, match="allow_existing"):
        command.upgrade(config, "head")
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def _alembic_config(database: Path, command_function, *x_arguments: str):
    from alembic.config import Config

    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(
        x=[f"db_url=sqlite:///{database.as_posix()}", *x_arguments],
        cmd=(command_function, (), {}),
    )
    return config


def test_existing_unversioned_baseline_cannot_be_upgraded_as_fresh(
    disposable_database_dir: Path,
):
    command = _alembic_command()
    database = disposable_database_dir / "unversioned-upgrade.db"
    _create_legacy_database(database)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    config = _alembic_config(database, command.upgrade, "allow_existing=true")

    with pytest.raises(RuntimeError, match="only be stamped"):
        command.upgrade(config, "head")
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_offline_upgrade_also_refuses_existing_unversioned_baseline(
    disposable_database_dir: Path,
):
    command = _alembic_command()
    database = disposable_database_dir / "offline-unversioned-upgrade.db"
    _create_legacy_database(database)
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    config = _alembic_config(database, command.upgrade, "allow_existing=true")

    with pytest.raises(RuntimeError, match="only be stamped"):
        command.upgrade(config, "head", sql=True)
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_existing_drifted_database_cannot_be_stamped_even_with_acknowledgement(
    disposable_database_dir: Path,
):
    command = _alembic_command()
    database = disposable_database_dir / "drifted-stamp.db"
    _create_schema_variant(database, confidence_type="TEXT")
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    config = _alembic_config(
        database,
        command.stamp,
        "allow_existing=true",
        "baseline_preflight=verified",
    )

    with pytest.raises(RuntimeError, match="did not pass exact"):
        command.stamp(config, "000000000001")
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_exact_existing_baseline_requires_explicit_verified_stamp_procedure(
    disposable_database_dir: Path,
):
    command = _alembic_command()
    database = disposable_database_dir / "exact-stamp.db"
    _create_legacy_database(database)

    without_token = _alembic_config(database, command.stamp, "allow_existing=true")
    with pytest.raises(RuntimeError, match="baseline_preflight=verified"):
        command.stamp(without_token, "000000000001")

    with_token = _alembic_config(
        database,
        command.stamp,
        "allow_existing=true",
        "baseline_preflight=verified",
    )
    command.stamp(with_token, "000000000001")
    report = preflight_database(database, allow_existing=True)
    assert report["status"] == "recognized_baseline_revision"
