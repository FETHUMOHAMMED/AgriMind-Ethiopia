# AgriMind-Ethiopia database migrations

The repository now has an Alembic migration foundation. Revision
`000000000001` represents only the verified legacy schema from the last
committed models: `users`, `predictions`, and `feedbacks`. Revision
`000000000002` is the first additive application upgrade and adds prediction
provenance columns only.

It intentionally does not create the Phase 1–4 tables or provenance columns.
Those require separately reviewed additive revisions.

The migration chain intentionally does not create the Phase 1-4 field-case,
consent, expert-review, or adjudication tables. Those require separately
reviewed additive revisions.

## Revision 000000000002: prediction provenance

Revision `000000000002` has parent `000000000001` and changes only the
`predictions` table:

- Adds nullable `image_sha256 VARCHAR(64)`. No existing image is hashed.
- Adds nullable `image_processing_history VARCHAR(2000)`. No historical
  processing history is inferred.
- Adds nullable `model_version VARCHAR(100)`. No version is inferred from a
  checkpoint or filename.
- Adds nullable `inference_timestamp DATETIME`.
- Adds the non-unique index `ix_predictions_image_sha256` on
  `predictions.image_sha256`.

The revision does not populate legacy rows, alter legacy columns or foreign
keys, inspect uploaded files, modify uploads, or add application-level data
validation rules. Legacy rows therefore retain `NULL` in all four new fields
until a later workflow records reliable evidence. The non-destructive
downgrade policy requires recovery from a verified backup rather than dropping
these columns. SQLite DDL is treated as non-transactional by Alembic, so the
revision cleans up only the objects it created when a DDL step fails. If that
cleanup fails, the database must be treated as partially migrated and restored
from the verified backup before retrying; it must not be stamped or reused.

The revision is not production-approved. Its migration tests must use newly
created disposable SQLite databases and an explicit legacy fixture; ORM
`Base.metadata.create_all()` is not a substitute for replaying the Alembic
chain.

## Baseline assumptions

The baseline is based on the committed model definitions, not on the current
Phase 1–4 working-tree models. It assumes:

- `users` contains the committed identity and role fields.
- `predictions` contains only the pre-Phase-4 prediction fields.
- `feedbacks` exists with its original user and prediction foreign keys.
- No historical consent, review, adjudication, taxonomy, or model provenance
  is inferred.

Existing databases must pass the exact read-only preflight before an operator
may stamp a baseline. The Alembic environment repeats that preflight itself;
the acknowledgement flag is not proof of schema correctness. This
implementation does not stamp any database automatically.

## Disposable fresh database

From any working directory, use an explicitly selected absolute disposable
path:

```text
alembic -c C:/projects/AgriMind-Ethiopia/backend/alembic.ini -x db_url=sqlite:///C:/temp/agrimind-fresh.db upgrade head
```

Relative paths, SQLite URI/query parameters, `backend/agrimind.db`, and
production paths are refused. The Alembic environment requires explicit target
selection and never reads `sqlalchemy.url` as a fallback.

## Read-only preflight

For an existing database, explicitly acknowledge that it may be inspected:

```text
python -m app.database.schema_preflight --database C:/temp/agrimind-copy.db --allow-existing
```

The command opens SQLite in read-only mode. It does not stamp, migrate,
repair, delete, merge, quarantine, or print row contents. Without
`--allow-existing`, an existing target is refused.

The development database is always refused by this command.

Preflight compares structured SQLite metadata: columns, declared types,
nullability, primary-key positions, defaults, indexes and their uniqueness,
columns, collation/order, origin and partial status, foreign-key endpoints and
actions, check expressions, table options, views, triggers, and the Alembic
version table. It normalizes whitespace and harmless outer parentheses rather
than comparing raw schema SQL. Features SQLite cannot establish reliably are
treated as mismatches or inspection refusals; expression-index SQL and
platform-specific filesystem identity remain SQLite/platform limitations.
Canonical paths and device/inode identity protect against symlink and hard-link
aliases where the operating system exposes reliable identity values.

## Migration history

Migration history can be inspected without selecting a database:

```text
alembic history
```

Commands that connect to a database must include an explicit absolute
`-x db_url=...` target. A fresh target must not already exist. Existing targets
additionally require `-x allow_existing=true`; an existing unversioned exact
legacy database may only be stamped with:

```text
alembic -c C:/projects/AgriMind-Ethiopia/backend/alembic.ini \
  -x db_url=sqlite:///C:/temp/verified-legacy.db \
  -x allow_existing=true -x baseline_preflight=verified \
  stamp 000000000001
```

The environment reruns exact preflight before accepting that command. Ordinary
`upgrade head` refuses an existing unversioned database. Unknown, partial, or
drifted schemas are refused in both online and offline modes. A versioned
baseline may be the source of a future additive upgrade, but stamping an
already-versioned target is refused.

For development verification of revision `000000000002`, use only a newly
created disposable database. Required checks include a fresh upgrade, an
exact legacy fixture with representative rows, preservation of legacy values
and row counts, NULL provenance fields on legacy predictions, storage of new
provenance values, index and foreign-key inspection, integrity checks, drift
rejection, refusal of silent upgrade/stamping, and an injected failure path
confirming that the revision is not recorded after a failed DDL step.

Do not run this revision against `backend/agrimind.db`, a production target,
or any existing user database during development. Do not use the migration to
backfill hashes, inspect historical uploads, infer model versions, or modify
credentials and uploaded images.

## Application startup

The application no longer calls `Base.metadata.create_all()` during normal
startup. Non-test startup requires `AGRIMIND_EXPECTED_SCHEMA_REVISION` to
identify a completed application schema revision. The legacy baseline is
explicitly rejected as sufficient for the current Phase 1–4 application.

`AGRIMIND_TESTING=1` is reserved for the isolated pytest fixture, which
creates its disposable test schema before importing the application.

## Future maintenance procedure

Before applying future revisions:

1. Stop application writes and use a maintenance window.
2. Back up the SQLite database consistently, including WAL state.
3. Back up associated uploads separately.
4. Restore the backup to a disposable location and run integrity and foreign
   key checks.
5. Run read-only preflight against the disposable copy.
6. Resolve duplicate or invalid records through an approved process; do not
   silently delete or merge them.
7. Apply the approved Alembic revisions with an explicit target.
8. Validate the revision, schema, row counts, foreign keys, and application
   smoke behavior before reopening writes.

Rollback should normally restore the verified backup. Destructive Alembic
downgrades are not a substitute for backup recovery because later revisions
may contain new data that a downgrade would destroy.

No production migration rollout is complete as part of this foundation task.

## Failure recovery — revision 000000000002

SQLite does not support transactional DDL. If revision 000000000002 fails
mid-upgrade, the migration attempts to clean up only the schema objects it
created (columns/index absent from the pre-migration schema).

### Automatic cleanup

Before running any DDL, the migration captures:

- The current column names of `predictions`
- The current index names of `predictions`

On failure, cleanup drops only columns and indexes that were **absent**
from the pre-migration snapshot. Anything that existed before the migration
started is never touched.

### Fail-closed guard

If any provenance column (`image_sha256`, `image_processing_history`,
`model_version`, `inference_timestamp`) already exists **before** this
migration starts, `upgrade()` aborts with a `RuntimeError` before any DDL
runs. This prevents accidental data loss from cleaning up an object the
migration did not create.

### Cleanup failure

If cleanup itself fails, `upgrade()` raises a `RuntimeError` with the message:

> "Prediction provenance migration failed and its partial DDL could not be
> cleaned up; restore the verified backup before retrying"

The operator MUST restore a verified backup before retrying. The database
must not be used in this state.

### Testing

The full failure behavior is covered by:

- `test_failed_revision_rolls_back_schema_and_revision_state` — injection of
  index-creation failure, verifies successful cleanup (revision stays at
  `000000000001`, all provenance columns removed)
- `test_cleanup_failure_raises_recovery_error` — injection of both
  index-creation AND cleanup failures, verifies the explicit recovery error
  is raised and the database is left at the pre-migration revision

### `downgrade()` behavior

`downgrade()` is intentionally **not** implemented as a data-destroying
operation. Running `alembic downgrade` on this revision raises a
`RuntimeError`. Restore a verified backup instead.

### SQLite version requirement

Cleanup uses `ALTER TABLE ... DROP COLUMN`, which requires **SQLite 3.35.0+**
(released March 2021). Python 3.10+ bundles compatible SQLite. On older
Python versions with older SQLite, cleanup will fail — triggering the
fail-closed recovery path described above. This is documented, not a bug.


## PostgreSQL migrations (Phase 3)

### Overview

The Alembic migration chain supports both SQLite and PostgreSQL. The revision
chain (`000000000001 → 000000000002 → ...`) is identical for both dialects.
Migration head is `000000000002` as of Phase 3 completion.

Migration behavior differences:

- **SQLite**: original implementation. Captures columns/indexes BEFORE any DDL
  runs and cleans up created objects on failure. Requires SQLite 3.35.0+ for
  `ALTER TABLE DROP COLUMN` during cleanup.
- **PostgreSQL**: uses `information_schema` and `pg_indexes` for inspection.
  PostgreSQL supports transactional DDL, so any failure inside `upgrade()`
  automatically rolls back the entire transaction — no explicit cleanup
  needed. The `_cleanup_partial_upgrade()` function is a no-op on PostgreSQL.

### Required flags for PostgreSQL

Every Alembic command against a PostgreSQL target MUST include:

| Flag | Purpose |
|---|---|
| `-x db_url=postgresql://...` | Explicit connection URL (existing requirement) |
| `-x expected_database=<name>` | Expected `current_database()` value |
| `-x expected_user=<name>` | Expected `current_user` value (must not be superuser) |
| `-x expected_schema=<name>` | Expected `current_schema()` value (default: `public`) |

The expected identity is supplied **independently** of the connection URL —
a target-switching attack (DNS rotation, load balancer redirect, proxy
rewrite) cannot convince the preflight to accept the wrong database.

### Connection identity verification

`guard_postgres_target()` verifies on the live connection:

- ✅ `current_database()` == `expected_database`
- ✅ `current_user` == `expected_user`
- ✅ `current_schema()` == `expected_schema`
- ✅ `current_user` is NOT a superuser (`rolsuper = false`)

**Logged but NOT compared:** `inet_server_addr()`, `inet_server_port()`.
In containerized, managed-database, or proxy-fronted deployments,
`inet_server_addr()` differs from the DNS name in the URL by design.
MITM protection is provided by TLS, not by server-IP comparison.

### TLS requirement in production

When `ENVIRONMENT=production`, the `DATABASE_URL` MUST include
`sslmode=verify-full`. This enables both certificate validation AND hostname
verification, preventing MITM attacks.

`sslmode=require` alone only encrypts the connection but does NOT verify the
server's hostname — a MITM with any valid certificate would pass.

There is no localhost exception. `ENVIRONMENT=production` + localhost + no
certificate is a misconfiguration that fails loudly.

### Fresh install on PostgreSQL

For a genuinely empty PostgreSQL database:

```text
alembic -c backend/alembic.ini \
  -x db_url=postgresql://agrimind_app:PASSWORD@HOST:5432/DBNAME \
  -x expected_database=DBNAME \
  -x expected_user=agrimind_app \
  -x expected_schema=public \
  -x allow_fresh=true \
  upgrade head


### Production migration invocation

In a production environment, running `alembic upgrade` requires BOTH:

1. **`DATABASE_URL` environment variable** — any valid PostgreSQL URL. This
   satisfies the application's production guard (raised at
   `app/database/database.py` import time when `ENVIRONMENT=production`).
   Without it, the import fails before Alembic's own checks run.
2. **`-x db_url=...` Alembic argument** — the actual migration target.

These should reference the SAME database. If they diverge, the guard passes
(DATABASE_URL is set) but migrations execute against a different target — a
subtle but real failure mode to avoid.

Example production invocation:

    DATABASE_URL="postgresql://agrimind_migrator:PASSWORD@host:5432/db" \
    alembic -c backend/alembic.ini \
      -x db_url="postgresql://agrimind_migrator:PASSWORD@host:5432/db?sslmode=verify-full" \
      -x expected_database=db \
      -x expected_user=agrimind_migrator \
      -x expected_schema=public \
      -x allow_existing=true \
      upgrade head

**Why this coupling exists:** `alembic/env.py` imports `Base` from
`app.database.database`, triggering that module's production guard. A future
phase may refactor this to a runtime `validate_production_config()` call so
that `alembic upgrade` can run without `DATABASE_URL` — the `-x db_url`
becomes the sole source of truth for the migration target. Deferred to a
later phase.