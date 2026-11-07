"""Alembic environment for explicitly selected SQLite databases."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app.database.database import Base
from app.database.schema_preflight import (
    LEGACY_BASELINE_REVISION,
    SchemaTargetError,
    guard_migration_target,
    preflight_database,
    sqlite_url_to_path,
)
from app.models import consent, expert_adjudication, expert_review, field_case, feedback, prediction, user


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _command_name() -> str | None:
    """Return the Alembic command name when invoked through the CLI/API."""

    command = getattr(config.cmd_opts, "cmd", None)
    if isinstance(command, tuple) and command:
        return getattr(command[0], "__name__", None)
    return None


def _revision_argument() -> str | None:
    try:
        revision = context.get_revision_argument()
    except Exception:
        return None
    if isinstance(revision, (tuple, list)):
        if len(revision) != 1:
            return None
        revision = revision[0]
    return str(revision) if revision is not None else None


def _gate_existing_target(path) -> None:
    """Require exact read-only preflight before any existing-target operation."""

    if not path.exists():
        return

    report = preflight_database(path, allow_existing=True)
    status = report["status"]
    command = _command_name()

    if status == "recognized_baseline_revision":
        if command == "stamp":
            raise SchemaTargetError(
                "Stamping an already versioned existing target is refused; use an upgrade"
            )
        return

    if status != "recognized_unversioned_legacy_baseline":
        raise SchemaTargetError(
            "Existing target did not pass exact legacy-baseline preflight; "
            "no migration or stamp was attempted"
        )

    # An unversioned existing database is never accepted by ordinary upgrade.
    # The explicit token records operator intent, but the exact preflight above
    # is the proof; the token alone cannot bypass the comparison.
    x_arguments = context.get_x_argument(as_dictionary=True)
    if (
        command != "stamp"
        or _revision_argument() != LEGACY_BASELINE_REVISION
        or x_arguments.get("baseline_preflight") != "verified"
    ):
        raise SchemaTargetError(
            "An exact unversioned legacy database may only be stamped with "
            "the explicit baseline_preflight=verified stamp procedure"
        )


def _explicit_target() -> str:
    arguments = context.get_x_argument(as_dictionary=True)
    db_url = arguments.get("db_url", "").strip()
    if not db_url:
        raise RuntimeError(
            "An explicit SQLite target is required: "
            "alembic -x db_url=sqlite:///ABSOLUTE/PATH.db ..."
        )
    path = sqlite_url_to_path(db_url)
    allow_existing = arguments.get("allow_existing", "false").lower() == "true"
    guard_migration_target(path, allow_existing=allow_existing)
    _gate_existing_target(path)
    return db_url


def run_migrations_offline() -> None:
    db_url = _explicit_target()
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    db_url = _explicit_target()
    connectable = create_engine(
        db_url,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
    )
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
