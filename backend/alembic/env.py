"""Alembic environment with explicit SQLite and PostgreSQL target validation.

Safety rules:
- Every migration target must be explicitly supplied with -x db_url=...
- SQLite retains its path/inode protections and exact legacy-baseline gate.
- PostgreSQL requires an independently supplied expected database identity.
- PostgreSQL targets are checked before migration execution or SQL generation.
- Production PostgreSQL requires sslmode=verify-full.
- Unknown database dialects fail closed.
- PostgreSQL offline migration generation is refused.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import NullPool

from app.database.database import Base
from app.database.schema_preflight import (
    LEGACY_BASELINE_REVISION,
    SchemaTargetError,
    guard_migration_target,
    preflight_database,
    sqlite_url_to_path,
)
from app.database.postgres_schema_preflight import (
    PgTargetIdentity,
    guard_postgres_target,
    preflight_postgres,
)
from app.models import (
    consent,
    expert_adjudication,
    expert_review,
    field_case,
    feedback,
    prediction,
    user,
)


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ============================================================================
# Command-line argument helpers
# ============================================================================


def _x_arguments() -> dict[str, str]:
    """Return all -x key=value arguments as a dict."""
    return context.get_x_argument(as_dictionary=True)


def _command_name() -> str | None:
    """Return the Alembic command name when invoked through the CLI/API."""
    command = getattr(config.cmd_opts, "cmd", None)
    if isinstance(command, tuple) and command:
        return getattr(command[0], "__name__", None)
    return None


def _revision_argument() -> str | None:
    """Return the target revision argument for stamp operations."""
    try:
        revision = context.get_revision_argument()
    except Exception:
        return None
    if isinstance(revision, (tuple, list)):
        if len(revision) != 1:
            return None
        revision = revision[0]
    return str(revision) if revision is not None else None


# ============================================================================
# SQLite existing-target gate (preserved from prior SQLite-only env.py)
# ============================================================================


def _gate_existing_target(path) -> None:
    """Require exact read-only preflight before any existing SQLite target op."""
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
    x_arguments = _x_arguments()
    if (
        command != "stamp"
        or _revision_argument() != LEGACY_BASELINE_REVISION
        or x_arguments.get("baseline_preflight") != "verified"
    ):
        raise SchemaTargetError(
            "An exact unversioned legacy database may only be stamped with "
            "the explicit baseline_preflight=verified stamp procedure"
        )


# ============================================================================
# PostgreSQL target identity, TLS, and gates
# ============================================================================


def _postgres_expected_identity() -> PgTargetIdentity:
    """Build PgTargetIdentity from explicit -x arguments.

    The expected identity is NOT inferred from the connection URL — it must
    be supplied independently so that a target-switching attack (or a
    load-balancer misroute) cannot convince the preflight to accept the wrong
    database.
    """
    arguments = _x_arguments()
    database = arguments.get("expected_database", "").strip()
    user = arguments.get("expected_user", "").strip()
    schema = arguments.get("expected_schema", "public").strip()
    if not database or not user or not schema:
        raise SchemaTargetError(
            "PostgreSQL requires explicit -x expected_database=..., "
            "-x expected_user=..., and -x expected_schema=..."
        )
    return PgTargetIdentity(database=database, user=user, schema=schema)


def _enforce_production_tls(url: URL) -> None:
    """Require sslmode=verify-full for every production PostgreSQL URL.

    No localhost exception. A local target combined with
    ENVIRONMENT=production is a misconfiguration that must fail loudly, not
    a legitimate deployment. sslmode=require alone does not verify hostname
    and is insufficient for MITM protection.
    """
    if os.getenv("ENVIRONMENT", "").strip().lower() != "production":
        return
    if not url.host:
        raise SchemaTargetError(
            "Production PostgreSQL requires a hostname"
        )
    if url.query.get("sslmode") != "verify-full":
        raise SchemaTargetError(
            "Production PostgreSQL requires sslmode=verify-full"
        )


def _gate_existing_postgres_target(
    url: URL, expected: PgTargetIdentity, *, allow_existing: bool
) -> None:
    """Require exact preflight before any existing PostgreSQL target operation.

    Mirrors _gate_existing_sqlite_target's fail-closed semantics for every
    status _derive_status() can produce.
    """
    report = preflight_postgres(url, expected=expected)
    status = report["status"]
    command = _command_name()
    arguments = _x_arguments()

    # Safety statuses — refused outright, no operator override.
    if status in {
        "cross_schema_fk_present",
        "invalid_indexes_present",
        "unvalidated_constraints_present",
    }:
        raise SchemaTargetError(
            f"PostgreSQL target has a safety violation: {status}. "
            "Migration refused. Investigate the database before retrying."
        )

    if status == "recognized_empty_database":
        # Fresh install: this is NOT an existing target, so allow_existing is
        # intentionally not required. Only allow_fresh=true is required.
        if command == "stamp":
            raise SchemaTargetError(
                "Stamping an empty PostgreSQL database is refused; use an upgrade"
            )
        if arguments.get("allow_fresh") != "true":
            raise SchemaTargetError(
                "A fresh empty PostgreSQL database requires explicit "
                "-x allow_fresh=true to authorize upgrade head"
            )
        return

    # Any status from here implies an EXISTING target (schema is present in
    # some form). Mirror SQLite's guard_migration_target policy: the operator
    # must explicitly acknowledge with -x allow_existing=true. This gate is
    # placed after recognized_empty_database so a truly fresh DB does not
    # require it.
    if not allow_existing:
        raise SchemaTargetError(
            f"PostgreSQL target status {status!r} indicates an existing database; "
            "-x allow_existing=true is required to proceed"
        )

    if status == "recognized_revision":
        if command == "stamp":
            raise SchemaTargetError(
                "Stamping an already versioned PostgreSQL target is refused; use an upgrade"
            )
        return

    if status == "recognized_unversioned_legacy_baseline":
        # Mirror SQLite: only exact baseline stamp with verified token
        if (
            command != "stamp"
            or _revision_argument() != LEGACY_BASELINE_REVISION
            or arguments.get("baseline_preflight") != "verified"
        ):
            raise SchemaTargetError(
                "An exact unversioned legacy PostgreSQL database may only be "
                "stamped with the explicit baseline_preflight=verified procedure"
            )
        return

    if status == "revision_drift":
        raise SchemaTargetError(
            "PostgreSQL target is at a known revision but its schema has drifted "
            "from the expected baseline for that revision. Migration refused."
        )

    # unknown_or_partial_schema or any future unrecognized status
    raise SchemaTargetError(
        f"PostgreSQL target did not pass preflight: status={status!r}. "
        "No migration or stamp was attempted."
    )


def _verify_postgres_migration_connection(
    connection, expected: PgTargetIdentity
) -> None:
    """Verify the ACTUAL Alembic migration connection's live identity.

    Distinct from the preflight connection (which uses its own engine and
    connection). The migration itself may connect to a different physical
    backend if a load balancer redirects, DNS rotates, or a proxy rewrites
    the route. This check runs on the connection that will execute DDL —
    closing that TOCTOU window.

    IMPORTANT — transaction boundary:
    SQLAlchemy 2.x autobegins a transaction on the first connection.execute().
    Without explicit closure, Alembic's subsequent context.begin_transaction()
    would fail with "a transaction is already begun on this Connection". We
    therefore wrap the identity query in an explicit `with connection.begin():`
    block that commits (or rolls back on error) and leaves the connection in
    a "no transaction" state before Alembic configures its migration
    transaction.

    Must be called before context.run_migrations().
    """
    with connection.begin():
        row = connection.execute(
            text(
                "SELECT current_database() AS db, "
                "       current_user AS usr, "
                "       current_schema() AS schema_name, "
                "       (SELECT rolsuper FROM pg_roles WHERE rolname = current_user) AS is_super"
            )
        ).mappings().one()
        if (
            row["db"] != expected.database
            or row["usr"] != expected.user
            or row["schema_name"] != expected.schema
        ):
            raise SchemaTargetError(
                "PostgreSQL migration connection identity mismatch: "
                f"actual(db={row['db']!r}, user={row['usr']!r}, "
                f"schema={row['schema_name']!r}) "
                f"expected(db={expected.database!r}, user={expected.user!r}, "
                f"schema={expected.schema!r})"
            )
        if row["is_super"]:
            raise SchemaTargetError(
                f"PostgreSQL migration connection uses superuser {row['usr']!r}; "
                "refusing. Use a dedicated migrator role."
            )


# ============================================================================
# Explicit target selection and dialect dispatch
# ============================================================================


def _explicit_target(
    *, offline: bool = False
) -> tuple[str, URL | None, PgTargetIdentity | None]:
    """Validate the explicitly selected migration target.

    Returns:
        (database_url, parsed_postgres_url, expected_postgres_identity)
    The URL and identity are None for SQLite.
    """
    arguments = _x_arguments()
    db_url = arguments.get("db_url", "").strip()
    if not db_url:
        raise SchemaTargetError(
            "An explicit migration target is required with -x db_url=..."
        )

    try:
        parsed = make_url(db_url)
    except Exception as exc:
        raise SchemaTargetError(f"Invalid database URL: {exc}") from exc

    backend = parsed.get_backend_name()

    if backend == "sqlite":
        path = sqlite_url_to_path(db_url)
        allow_existing = arguments.get("allow_existing", "false").lower() == "true"
        guard_migration_target(path, allow_existing=allow_existing)
        _gate_existing_target(path)
        return db_url, None, None

    if backend == "postgresql":
        if offline:
            raise SchemaTargetError(
                "PostgreSQL offline migration generation is refused: "
                "offline SQL cannot verify the live target connection "
                "that will eventually receive the generated DDL."
            )
        _enforce_production_tls(parsed)
        expected = _postgres_expected_identity()
        allow_existing = arguments.get("allow_existing", "false").lower() == "true"
        guard_postgres_target(parsed, expected=expected)
        _gate_existing_postgres_target(parsed, expected, allow_existing=allow_existing)
        return db_url, parsed, expected

    raise SchemaTargetError(
        f"Unsupported database dialect: {backend!r}. "
        "Only sqlite:// and postgresql:// are supported."
    )


# ============================================================================
# Migration entry points
# ============================================================================


def run_migrations_offline() -> None:
    db_url, _parsed_pg, _expected_pg = _explicit_target(offline=True)
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    db_url, parsed_pg, expected_pg = _explicit_target(offline=False)

    # Conditional connect_args and poolclass — SQLite-only settings never
    # reach psycopg2 (which rejects check_same_thread). PostgreSQL uses
    # SQLAlchemy's default pool, appropriate for migration workloads.
    engine_kwargs: dict = {}
    if parsed_pg is None:
        # SQLite
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = NullPool
    else:
        # PostgreSQL — no SQLite-specific kwargs
        engine_kwargs["connect_args"] = {}

    connectable = create_engine(db_url, **engine_kwargs)
    try:
        with connectable.connect() as connection:
            if parsed_pg is not None:
                # PostgreSQL: verify live identity on the actual migration
                # connection before running any DDL. This closes the
                # preflight-vs-migration TOCTOU window.
                assert expected_pg is not None
                _verify_postgres_migration_connection(connection, expected_pg)
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
