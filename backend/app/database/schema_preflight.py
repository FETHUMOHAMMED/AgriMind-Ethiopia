"""Read-only SQLite schema inspection and migration-target guards.

The baseline comparison deliberately uses structured SQLite metadata instead
of comparing raw ``CREATE TABLE`` SQL. SQLite can emit equivalent SQL with
different whitespace or parenthesization, while PRAGMA metadata gives stable
semantic values for columns, indexes, foreign keys, and primary keys. The
remaining table-definition features that SQLite does not expose through those
PRAGMAs are detected from schema SQL and cause a mismatch when they are not
part of the committed baseline.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import unquote


LEGACY_BASELINE_REVISION = "000000000001"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEVELOPMENT_DATABASE = (_REPOSITORY_ROOT / "backend" / "agrimind.db").resolve()
_ALEMBIC_VERSION_TABLE = "alembic_version"


def _column(
    declared_type: str,
    *,
    nullable: bool,
    primary_key: int = 0,
    default: str | None = None,
) -> dict[str, Any]:
    return {
        "type": declared_type,
        "nullable": nullable,
        "primary_key": primary_key,
        "default": default,
        "hidden": 0,
    }


def _index(
    *,
    unique: bool,
    columns: tuple[str, ...],
    partial: bool = False,
    origin: str = "c",
) -> dict[str, Any]:
    return {
        "unique": unique,
        "columns": columns,
        "index_columns": tuple((column, False, "BINARY") for column in columns),
        "partial": partial,
        "origin": origin,
    }


# Derived from the last committed models at HEAD, not from the additive
# working-tree models. language/role defaults were ORM client-side defaults,
# so they are intentionally not database server defaults here.
LEGACY_BASELINE: dict[str, Any] = {
    "users": {
        "columns": {
            "id": _column("INTEGER", nullable=False, primary_key=1),
            "full_name": _column("VARCHAR", nullable=False),
            "email": _column("VARCHAR", nullable=False),
            "phone": _column("VARCHAR", nullable=True),
            "password_hash": _column("VARCHAR", nullable=False),
            "language": _column("VARCHAR", nullable=True),
            "role": _column("VARCHAR", nullable=True),
            "created_at": _column("DATETIME", nullable=True, default="CURRENT_TIMESTAMP"),
        },
        "indexes": {
            "ix_users_email": _index(unique=True, columns=("email",)),
            "ix_users_id": _index(unique=False, columns=("id",)),
        },
        "foreign_keys": set(),
        "checks": (),
        "table_features": (),
    },
    "predictions": {
        "columns": {
            "id": _column("INTEGER", nullable=False, primary_key=1),
            "user_id": _column("INTEGER", nullable=False),
            "image_url": _column("VARCHAR", nullable=True),
            "disease": _column("VARCHAR", nullable=False),
            "confidence": _column("FLOAT", nullable=True),
            "recommendation": _column("VARCHAR", nullable=True),
            "created_at": _column("DATETIME", nullable=True, default="CURRENT_TIMESTAMP"),
        },
        "indexes": {
            "ix_predictions_id": _index(unique=False, columns=("id",)),
        },
        "foreign_keys": {
            ("user_id", "users", "id", "NO ACTION", "NO ACTION"),
        },
        "checks": (),
        "table_features": (),
    },
    "feedbacks": {
        "columns": {
            "id": _column("INTEGER", nullable=False, primary_key=1),
            "user_id": _column("INTEGER", nullable=False),
            "prediction_id": _column("INTEGER", nullable=False),
            "correct": _column("BOOLEAN", nullable=False),
            "comment": _column("VARCHAR", nullable=True),
            "created_at": _column("DATETIME", nullable=True, default="CURRENT_TIMESTAMP"),
        },
        "indexes": {
            "ix_feedbacks_id": _index(unique=False, columns=("id",)),
        },
        "foreign_keys": {
            ("user_id", "users", "id", "NO ACTION", "NO ACTION"),
            ("prediction_id", "predictions", "id", "NO ACTION", "NO ACTION"),
        },
        "checks": (),
        "table_features": (),
    },
}

_ALEMBIC_VERSION_BASELINE = {
    "columns": {"version_num": _column("VARCHAR(32)", nullable=False, primary_key=1)},
    "indexes": {
        "sqlite_autoindex_alembic_version_1": _index(
            unique=True, columns=("version_num",), origin="pk"
        )
    },
    "foreign_keys": set(),
    "checks": (),
    "table_features": (),
}


class SchemaTargetError(RuntimeError):
    """Raised when a target is ambiguous, protected, or cannot be inspected."""


def sqlite_url_to_path(database_url: str) -> Path:
    """Convert an explicit absolute on-disk SQLite URL into a path."""

    if not database_url.startswith("sqlite:///") or database_url.startswith("sqlite+"):
        raise SchemaTargetError("Only explicit sqlite:/// database URLs are supported")
    raw_target = database_url[len("sqlite:///") :]
    if "?" in raw_target or "#" in raw_target:
        raise SchemaTargetError("SQLite target URLs must not contain query or fragment parameters")
    raw_path = unquote(raw_target)
    if not raw_path or raw_path in {":memory:", "file::memory:"} or raw_path.startswith("file:"):
        raise SchemaTargetError("An absolute on-disk SQLite database path is required")
    path = Path(raw_path)
    if not path.is_absolute():
        raise SchemaTargetError("The SQLite database path must be absolute")
    return path.resolve(strict=False)


def _file_identity(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    device = int(getattr(stat, "st_dev", 0))
    inode = int(getattr(stat, "st_ino", 0))
    if device <= 0 or inode <= 0:
        return None
    return device, inode


def guard_migration_target(path: Path, *, allow_existing: bool) -> None:
    """Guard an explicitly selected migration target without opening it."""

    resolved = path.resolve(strict=False)
    if resolved == DEVELOPMENT_DATABASE:
        raise SchemaTargetError(
            "The development database is protected and cannot be selected by this command"
        )
    if resolved.exists() and not resolved.is_file():
        raise SchemaTargetError("The selected database target is not a regular file")

    # Canonical paths catch symlinks. File identity additionally catches hard
    # links when the filesystem exposes reliable device/inode values.
    if resolved.exists() and DEVELOPMENT_DATABASE.exists():
        target_identity = _file_identity(resolved)
        development_identity = _file_identity(DEVELOPMENT_DATABASE)
        if target_identity is None or development_identity is None:
            raise SchemaTargetError(
                "Could not establish protected-database identity safely; target refused"
            )
        if target_identity == development_identity:
            raise SchemaTargetError(
                "The selected target aliases the protected development database"
            )

    if resolved.exists() and not allow_existing:
        raise SchemaTargetError(
            "An existing database requires explicit allow_existing=true; "
            "no migration or stamp was attempted"
        )
    if not resolved.exists() and not resolved.parent.exists():
        raise SchemaTargetError("The selected database parent directory does not exist")


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _read_only_connection(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)


def _normalize_type(value: Any) -> str:
    return " ".join(str(value or "").strip().upper().split())


def _normalize_sql_fragment(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    while text.startswith("(") and text.endswith(")"):
        depth = 0
        balanced_outer = True
        quote: str | None = None
        for index, character in enumerate(text):
            if quote:
                if character == quote and (index == 0 or text[index - 1] != "\\"):
                    quote = None
                continue
            if character in {"'", '"', "`"}:
                quote = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and index != len(text) - 1:
                    balanced_outer = False
                    break
        if balanced_outer and depth == 0 and quote is None:
            text = text[1:-1].strip()
        else:
            break
    if "'" not in text and '"' not in text and "`" not in text:
        return text.upper()
    return text


def _table_info(connection: sqlite3.Connection, table: str) -> dict[str, dict[str, Any]]:
    rows = connection.execute(f"PRAGMA table_xinfo({_quote_identifier(table)})").fetchall()
    return {
        str(row[1]): {
            "type": _normalize_type(row[2]),
            "nullable": not bool(row[3]),
            "primary_key": int(row[5]),
            "default": _normalize_sql_fragment(row[4]),
            "hidden": int(row[6]) if len(row) > 6 else 0,
        }
        for row in rows
    }


def _index_info(connection: sqlite3.Connection, table: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    rows = connection.execute(f"PRAGMA index_list({_quote_identifier(table)})").fetchall()
    for row in rows:
        index_name = str(row[1])
        xinfo_rows = connection.execute(
            f"PRAGMA index_xinfo({_quote_identifier(index_name)})"
        ).fetchall()
        index_columns = tuple(
            (
                str(index_row[2]) if index_row[2] is not None else "<expression>",
                bool(index_row[3]) if len(index_row) > 3 else False,
                _normalize_type(index_row[4]) or "BINARY",
            )
            for index_row in xinfo_rows
            if len(index_row) < 6 or bool(index_row[5])
        )
        result[index_name] = {
            "unique": bool(row[2]),
            "columns": tuple(column for column, _, _ in index_columns),
            "index_columns": index_columns,
            "partial": bool(row[4]) if len(row) > 4 else False,
            "origin": str(row[3]).lower() if len(row) > 3 else "c",
        }
    return result


def _foreign_key_info(connection: sqlite3.Connection, table: str) -> set[tuple[str, str, str, str, str]]:
    return {
        (
            str(row[3]),
            str(row[2]),
            str(row[4]),
            str(row[6]).upper(),
            str(row[5]).upper(),
        )
        for row in connection.execute(f"PRAGMA foreign_key_list({_quote_identifier(table)})").fetchall()
    }


def _find_matching_parenthesis(text: str, opening: int) -> int | None:
    depth = 0
    quote: str | None = None
    for index in range(opening, len(text)):
        character = text[index]
        if quote:
            if character == quote and (index == 0 or text[index - 1] != "\\"):
                quote = None
            continue
        if character in {"'", '"', "`"}:
            quote = character
        elif character == "[":
            quote = "]"
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index
    return None


def _check_constraints(table_sql: str | None) -> tuple[tuple[str, ...], bool]:
    if not table_sql:
        return (), False
    checks: list[str] = []
    upper = table_sql.upper()
    cursor = 0
    quote: str | None = None
    while cursor < len(table_sql):
        character = table_sql[cursor]
        if quote:
            if character == quote and (cursor == 0 or table_sql[cursor - 1] != "\\"):
                quote = None
            cursor += 1
            continue
        if character in {"'", '"', "`"}:
            quote = character
            cursor += 1
            continue
        match = re.search(r"\bCHECK\s*\(", upper[cursor:])
        if not match:
            break
        opening = cursor + match.end() - 1
        closing = _find_matching_parenthesis(table_sql, opening)
        if closing is None:
            return (), False
        checks.append(_normalize_sql_fragment(table_sql[opening + 1 : closing]) or "")
        cursor = closing + 1
    return tuple(sorted(checks)), True


def _table_features(table_sql: str | None) -> tuple[str, ...]:
    if not table_sql:
        return ("missing_table_sql",)
    upper = table_sql.upper()
    features: list[str] = []
    if re.search(r"\bWITHOUT\s+ROWID\b", upper):
        features.append("without_rowid")
    if re.search(r"\)\s*STRICT\s*$", upper):
        features.append("strict")
    if re.search(r"\bAUTOINCREMENT\b", upper):
        features.append("autoincrement")
    if re.search(r"\bCOLLATE\b", upper):
        features.append("collation")
    if re.search(r"\bGENERATED\b|\bVIRTUAL\b|\bSTORED\b", upper):
        features.append("generated_column")
    if re.search(r"\bON\s+CONFLICT\b", upper):
        features.append("conflict_policy")
    if re.search(r"\bMATCH\b|\bDEFERRABLE\b|\bINITIALLY\b", upper):
        features.append("foreign_key_options")
    return tuple(sorted(set(features)))


def _read_schema_objects(
    connection: sqlite3.Connection,
) -> tuple[dict[str, dict[str, str | None]], set[str], set[str]]:
    rows = connection.execute(
        "SELECT name, type, sql FROM sqlite_master "
        "WHERE type IN ('table', 'view', 'trigger') "
        "AND name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    objects = {str(row[0]): {"type": str(row[1]), "sql": row[2]} for row in rows}
    tables = {name for name, data in objects.items() if data["type"] == "table"}
    views = {name for name, data in objects.items() if data["type"] == "view"}
    triggers = {name for name, data in objects.items() if data["type"] == "trigger"}
    return objects, tables, views | triggers


def _inspect_table(connection: sqlite3.Connection, table: str, sql: str | None) -> dict[str, Any]:
    checks, checks_parseable = _check_constraints(sql)
    return {
        "columns": _table_info(connection, table),
        "indexes": _index_info(connection, table),
        "foreign_keys": _foreign_key_info(connection, table),
        "checks": checks,
        "checks_parseable": checks_parseable,
        "table_features": _table_features(sql),
    }


def _diff_mapping(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    expected_names = set(expected)
    actual_names = set(actual)
    return {
        "missing": sorted(expected_names - actual_names),
        "unexpected": sorted(actual_names - expected_names),
        "changed": {
            name: {"expected": expected[name], "actual": actual[name]}
            for name in sorted(expected_names & actual_names)
            if expected[name] != actual[name]
        },
    }


def _compare_baseline(
    tables: dict[str, dict[str, Any]],
    actual_table_names: set[str],
    *,
    views: set[str],
    triggers: set[str],
    objects: dict[str, dict[str, str | None]],
) -> dict[str, Any]:
    expected_table_names = set(LEGACY_BASELINE)
    application_tables = actual_table_names - {_ALEMBIC_VERSION_TABLE}
    missing_tables = sorted(expected_table_names - application_tables)
    unexpected_tables = sorted(application_tables - expected_table_names)
    missing_columns: dict[str, list[str]] = {}
    unexpected_columns: dict[str, list[str]] = {}
    column_mismatches: dict[str, dict[str, Any]] = {}
    missing_indexes: dict[str, list[str]] = {}
    unexpected_indexes: dict[str, list[str]] = {}
    index_mismatches: dict[str, dict[str, Any]] = {}
    foreign_key_mismatches: dict[str, dict[str, list[Any]]] = {}
    check_constraint_mismatches: dict[str, dict[str, Any]] = {}
    table_definition_mismatches: dict[str, dict[str, Any]] = {}

    for table, expected in LEGACY_BASELINE.items():
        if table not in tables:
            continue
        actual = tables[table]
        column_diff = _diff_mapping(expected["columns"], actual["columns"])
        if column_diff["missing"]:
            missing_columns[table] = column_diff["missing"]
        if column_diff["unexpected"]:
            unexpected_columns[table] = column_diff["unexpected"]
        if column_diff["changed"]:
            column_mismatches[table] = column_diff["changed"]

        index_diff = _diff_mapping(expected["indexes"], actual["indexes"])
        if index_diff["missing"]:
            missing_indexes[table] = index_diff["missing"]
        if index_diff["unexpected"]:
            unexpected_indexes[table] = index_diff["unexpected"]
        if index_diff["changed"]:
            index_mismatches[table] = index_diff["changed"]

        expected_fks = expected["foreign_keys"]
        actual_fks = actual["foreign_keys"]
        if actual_fks != expected_fks:
            foreign_key_mismatches[table] = {
                "missing": sorted(expected_fks - actual_fks),
                "unexpected": sorted(actual_fks - expected_fks),
            }

        if actual["checks"] != expected["checks"] or not actual["checks_parseable"]:
            check_constraint_mismatches[table] = {
                "expected": expected["checks"],
                "actual": actual["checks"],
                "parseable": actual["checks_parseable"],
            }
        if actual["table_features"] != expected["table_features"]:
            table_definition_mismatches[table] = {
                "expected_features": expected["table_features"],
                "actual_features": actual["table_features"],
            }

    alembic_version_mismatch: dict[str, Any] = {}
    if _ALEMBIC_VERSION_TABLE in tables:
        version_diff = _diff_mapping(
            _ALEMBIC_VERSION_BASELINE["columns"],
            tables[_ALEMBIC_VERSION_TABLE]["columns"],
        )
        version_indexes = _diff_mapping(
            _ALEMBIC_VERSION_BASELINE["indexes"],
            tables[_ALEMBIC_VERSION_TABLE]["indexes"],
        )
        if any(version_indexes.values()):
            version_diff["indexes"] = version_indexes
        if any(version_diff.values()):
            alembic_version_mismatch = version_diff
        version_sql = objects.get(_ALEMBIC_VERSION_TABLE, {}).get("sql")
        if not tables[_ALEMBIC_VERSION_TABLE]["checks_parseable"] or _table_features(version_sql):
            alembic_version_mismatch["table_features"] = _table_features(version_sql)

    unexpected_views = sorted(views)
    unexpected_triggers = sorted(triggers)
    exact = not (
        missing_tables
        or unexpected_tables
        or missing_columns
        or unexpected_columns
        or column_mismatches
        or missing_indexes
        or unexpected_indexes
        or index_mismatches
        or foreign_key_mismatches
        or check_constraint_mismatches
        or table_definition_mismatches
        or alembic_version_mismatch
        or unexpected_views
        or unexpected_triggers
    )
    return {
        "matches_known_baseline": exact,
        "missing_tables": missing_tables,
        "unexpected_tables": unexpected_tables,
        "missing_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "column_mismatches": column_mismatches,
        "missing_indexes": missing_indexes,
        "unexpected_indexes": unexpected_indexes,
        "index_mismatches": index_mismatches,
        "foreign_key_mismatches": foreign_key_mismatches,
        "check_constraint_mismatches": check_constraint_mismatches,
        "table_definition_mismatches": table_definition_mismatches,
        "unexpected_views": unexpected_views,
        "unexpected_triggers": unexpected_triggers,
        "alembic_version_mismatch": alembic_version_mismatch,
    }


def _read_revision(connection: sqlite3.Connection) -> list[str]:
    table_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
    ).fetchone()
    if not table_exists:
        return []
    return [str(row[0]) for row in connection.execute("SELECT version_num FROM alembic_version")]


def preflight_database(path: Path, *, allow_existing: bool = False) -> dict[str, Any]:
    """Inspect a selected SQLite database without opening it for write."""

    path = path.resolve(strict=False)
    guard_migration_target(path, allow_existing=allow_existing)
    if not path.exists():
        raise SchemaTargetError("The selected database does not exist; preflight did not create it")

    try:
        connection = _read_only_connection(path)
    except sqlite3.Error as exc:
        raise SchemaTargetError("The selected database could not be opened read-only") from exc

    try:
        try:
            objects, table_names, non_table_objects = _read_schema_objects(connection)
            views = {name for name, data in objects.items() if data["type"] == "view"}
            triggers = {name for name, data in objects.items() if data["type"] == "trigger"}
            tables = {
                table: _inspect_table(connection, table, objects[table]["sql"])
                for table in sorted(table_names)
            }
            integrity_ok = connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            foreign_key_violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
            revisions = _read_revision(connection)
            comparison = _compare_baseline(
                tables,
                table_names,
                views=views,
                triggers=triggers,
                objects=objects,
            )
        except sqlite3.Error as exc:
            raise SchemaTargetError(
                "SQLite schema inspection failed; equivalence was not established"
            ) from exc

        if comparison["matches_known_baseline"] and revisions == [LEGACY_BASELINE_REVISION]:
            status = "recognized_baseline_revision"
        elif comparison["matches_known_baseline"] and not revisions:
            status = "recognized_unversioned_legacy_baseline"
        elif revisions == [LEGACY_BASELINE_REVISION]:
            status = "revision_drift"
        else:
            status = "unknown_or_partial_schema"

        return {
            "database": str(path),
            "status": status,
            "alembic_revisions": revisions,
            "integrity_check_ok": integrity_ok,
            "foreign_key_violation_count": foreign_key_violations,
            "check_constraint_tables": sorted(
                table for table, data in tables.items() if data["checks"]
            ),
            "tables": {
                table: {
                    "columns": data["columns"],
                    "indexes": [
                        {"name": name, **index}
                        for name, index in sorted(data["indexes"].items())
                    ],
                    "foreign_keys": [
                        {
                            "column": column,
                            "referenced_table": ref_table,
                            "referenced_column": ref_column,
                            "on_delete": on_delete,
                            "on_update": on_update,
                        }
                        for column, ref_table, ref_column, on_delete, on_update
                        in sorted(data["foreign_keys"])
                    ],
                    "check_constraints": list(data["checks"]),
                    "table_features": list(data["table_features"]),
                }
                for table, data in sorted(tables.items())
            },
            "schema_objects": {
                "views": sorted(views),
                "triggers": sorted(triggers),
                "non_table_objects": sorted(non_table_objects),
            },
            **comparison,
        }
    finally:
        connection.close()


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only AgriMind SQLite schema preflight")
    parser.add_argument("--database", required=True, type=Path, help="Explicit SQLite database path")
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Acknowledge that the selected existing database may be inspected read-only",
    )
    args = parser.parse_args(argv)
    try:
        report = preflight_database(args.database, allow_existing=args.allow_existing)
    except SchemaTargetError as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, default=list))
    return 0 if report["status"].startswith("recognized_") and report["integrity_check_ok"] and report["foreign_key_violation_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_main())
