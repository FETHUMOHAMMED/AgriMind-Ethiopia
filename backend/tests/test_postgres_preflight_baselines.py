"""Focused unit tests for PostgreSQL revision baselines (Step 3.2.1).

These tests do NOT require a PostgreSQL connection — they use in-memory
inspected schema dicts to exercise _compare_baseline_pg and
_compare_against_revision directly. Verified offline; no migration executed.
"""
import copy

import pytest

from app.database.schema_preflight import SchemaTargetError
from app.database.postgres_schema_preflight import (
    LEGACY_BASELINE_PG,
    REVISION_BASELINES_PG,
    _REVISION_0002_BASELINE,
    _compare_against_revision,
    _compute_is_fully_empty,     # ← ADD
    _derive_status,              # ← ADD
)


def _inspected_from_baseline(baseline):
    """Build an `inspected` schema dict from a baseline dict, mirroring how
    _inspect_table + _get_columns/_get_indexes/_get_foreign_keys/_get_checks
    would populate `inspected` for a database matching the baseline exactly."""
    inspected = {}
    for table, spec in baseline.items():
        inspected[table] = {
            "columns": copy.deepcopy(spec["columns"]),
            "indexes": copy.deepcopy(spec["indexes"]),
            "foreign_keys": set(spec["foreign_keys"]),
            "checks": tuple(spec["checks"]),
        }
    return inspected


class TestDeepCopyIsolation:
    def test_revision_0002_columns_do_not_leak_into_legacy(self):
        assert "image_sha256" not in LEGACY_BASELINE_PG["predictions"]["columns"]
        assert "image_sha256" in _REVISION_0002_BASELINE["predictions"]["columns"]

    def test_revision_0002_indexes_do_not_leak_into_legacy(self):
        assert "ix_predictions_image_sha256" not in LEGACY_BASELINE_PG["predictions"]["indexes"]
        assert "ix_predictions_image_sha256" in _REVISION_0002_BASELINE["predictions"]["indexes"]

    def test_legacy_unchanged_after_import(self):
        assert set(LEGACY_BASELINE_PG.keys()) == {"users", "predictions", "feedbacks"}
        assert len(LEGACY_BASELINE_PG["users"]["columns"]) == 8
        assert len(LEGACY_BASELINE_PG["predictions"]["columns"]) == 7
        assert len(LEGACY_BASELINE_PG["feedbacks"]["columns"]) == 6

    def test_mutating_revision_0002_does_not_affect_legacy(self):
        # Mutate the copy and verify legacy is unaffected
        original_legacy_email_type = LEGACY_BASELINE_PG["users"]["columns"]["email"]["type"]
        _REVISION_0002_BASELINE["users"]["columns"]["email"]["type"] = "TEXT"
        try:
            assert LEGACY_BASELINE_PG["users"]["columns"]["email"]["type"] == original_legacy_email_type
        finally:
            _REVISION_0002_BASELINE["users"]["columns"]["email"]["type"] = original_legacy_email_type


class TestRevisionBaselinesRegistry:
    def test_revision_0001_is_legacy_baseline(self):
        assert REVISION_BASELINES_PG["000000000001"] is LEGACY_BASELINE_PG

    def test_revision_0002_is_registered(self):
        assert "000000000002" in REVISION_BASELINES_PG
        assert REVISION_BASELINES_PG["000000000002"] is _REVISION_0002_BASELINE


class TestRevision0002Structure:
    def test_has_all_four_provenance_columns(self):
        cols = _REVISION_0002_BASELINE["predictions"]["columns"]
        for name in ("image_sha256", "image_processing_history", "model_version", "inference_timestamp"):
            assert name in cols

    def test_varchar_lengths_explicit(self):
        cols = _REVISION_0002_BASELINE["predictions"]["columns"]
        assert cols["image_sha256"]["type"] == "character varying(64)"
        assert cols["image_processing_history"]["type"] == "character varying(2000)"
        assert cols["model_version"]["type"] == "character varying(100)"

    def test_inference_timestamp_type(self):
        cols = _REVISION_0002_BASELINE["predictions"]["columns"]
        assert cols["inference_timestamp"]["type"] == "timestamp with time zone"

    def test_has_provenance_index(self):
        indexes = _REVISION_0002_BASELINE["predictions"]["indexes"]
        assert "ix_predictions_image_sha256" in indexes
        assert indexes["ix_predictions_image_sha256"] == {
            "unique": False,
            "columns": ("image_sha256",),
        }

    def test_all_provenance_columns_nullable(self):
        cols = _REVISION_0002_BASELINE["predictions"]["columns"]
        for name in ("image_sha256", "image_processing_history", "model_version", "inference_timestamp"):
            assert cols[name]["nullable"] is True, f"{name} should be nullable"


class TestRevision0001Comparison:
    def test_exact_match(self):
        inspected = _inspected_from_baseline(LEGACY_BASELINE_PG)
        result = _compare_against_revision("000000000001", inspected, set(inspected.keys()))
        assert result["matches_known_baseline"] is True
        assert result["missing_tables"] == []
        assert result["unexpected_tables"] == []
        assert result["column_mismatches"] == {}


class TestRevision0002Comparison:
    def test_exact_match(self):
        inspected = _inspected_from_baseline(_REVISION_0002_BASELINE)
        result = _compare_against_revision("000000000002", inspected, set(inspected.keys()))
        assert result["matches_known_baseline"] is True
        assert result["missing_columns"] == {}
        assert result["unexpected_columns"] == {}
        assert result["missing_indexes"] == {}
        assert result["unexpected_indexes"] == {}

    def test_legacy_schema_fails_revision_0002(self):
        """A legacy-only schema (no provenance columns) must NOT match revision 0002."""
        inspected = _inspected_from_baseline(LEGACY_BASELINE_PG)
        result = _compare_against_revision("000000000002", inspected, set(inspected.keys()))
        assert result["matches_known_baseline"] is False
        assert "image_sha256" in result["missing_columns"]["predictions"]
        assert "ix_predictions_image_sha256" in result["missing_indexes"]["predictions"]


class TestRevision0002Mismatches:
    def _inspected(self):
        return _inspected_from_baseline(_REVISION_0002_BASELINE)

    def test_missing_provenance_column_detected(self):
        inspected = self._inspected()
        del inspected["predictions"]["columns"]["image_sha256"]
        result = _compare_against_revision("000000000002", inspected, set(inspected.keys()))
        assert result["matches_known_baseline"] is False
        assert "image_sha256" in result["missing_columns"]["predictions"]

    def test_incorrect_varchar_length_detected(self):
        inspected = self._inspected()
        inspected["predictions"]["columns"]["image_sha256"]["type"] = "character varying"
        result = _compare_against_revision("000000000002", inspected, set(inspected.keys()))
        assert result["matches_known_baseline"] is False
        assert "image_sha256" in result["column_mismatches"]["predictions"]

    def test_missing_provenance_index_detected(self):
        inspected = self._inspected()
        del inspected["predictions"]["indexes"]["ix_predictions_image_sha256"]
        result = _compare_against_revision("000000000002", inspected, set(inspected.keys()))
        assert result["matches_known_baseline"] is False
        assert "ix_predictions_image_sha256" in result["missing_indexes"]["predictions"]

    def test_unexpected_extra_column_detected(self):
        inspected = self._inspected()
        inspected["predictions"]["columns"]["unexpected_extra"] = {
            "type": "character varying",
            "nullable": True,
            "primary_key": False,
            "default": None,
            "id_generation": "plain",
        }
        result = _compare_against_revision("000000000002", inspected, set(inspected.keys()))
        assert result["matches_known_baseline"] is False
        assert "unexpected_extra" in result["unexpected_columns"]["predictions"]


class TestUnknownRevision:
    def test_unknown_revision_raises(self):
        inspected = _inspected_from_baseline(LEGACY_BASELINE_PG)
        with pytest.raises(SchemaTargetError, match="No schema baseline defined"):
            _compare_against_revision("999999999999", inspected, set(inspected.keys()))
            

class TestStep322AcceptanceCriteria:
    """Step 3.2.2 acceptance criteria — all testable via _derive_status and
    _compute_is_fully_empty without a live PostgreSQL connection."""


    def test_1_fresh_empty_database_recognized(self):
        """Criterion 1: fresh empty DB → recognized_empty_database."""
        is_fully_empty = _compute_is_fully_empty(
            current_revision_status="no_revision",
            revisions=[],
            inspected={},
            table_names=set(),
        )
        status = _derive_status(
            cross_schema_fks=[], invalid_indexes=[], unvalidated=[],
            is_fully_empty=is_fully_empty,
            current_revision_status="no_revision",
            matches_known_baseline=False,
        )
        assert status == "recognized_empty_database"

    def test_2_legacy_schema_without_revision_recognized(self):
        """Criterion 2: legacy schema, no revision → recognized_unversioned_legacy_baseline."""
        # Legacy DB: has tables (users, predictions, feedbacks), no revision
        is_fully_empty = _compute_is_fully_empty(
            current_revision_status="no_revision",
            revisions=[],
            inspected={"users": {}, "predictions": {}, "feedbacks": {}},
            table_names={"users", "predictions", "feedbacks"},
        )
        assert is_fully_empty is False
        status = _derive_status(
            cross_schema_fks=[], invalid_indexes=[], unvalidated=[],
            is_fully_empty=is_fully_empty,
            current_revision_status="no_revision",
            matches_known_baseline=True,
        )
        assert status == "recognized_unversioned_legacy_baseline"

    def test_3_empty_alembic_version_table_refused(self):
        """Criterion 3: empty alembic_version table (zero rows) → refused.

        table_names contains alembic_version; inspected excludes it; revisions is empty.
        The `not table_names` condition must prevent is_fully_empty=True."""
        is_fully_empty = _compute_is_fully_empty(
            current_revision_status="no_revision",
            revisions=[],
            inspected={},                          # alembic_version excluded
            table_names={"alembic_version"},      # but present in catalog
        )
        assert is_fully_empty is False
        status = _derive_status(
            cross_schema_fks=[], invalid_indexes=[], unvalidated=[],
            is_fully_empty=is_fully_empty,
            current_revision_status="no_revision",
            matches_known_baseline=False,
        )
        assert status == "unknown_or_partial_schema"

    def test_4_partial_application_schema_refused(self):
        """Criterion 4: partial application schema → unknown_or_partial_schema."""
        is_fully_empty = _compute_is_fully_empty(
            current_revision_status="no_revision",
            revisions=[],
            inspected={"users": {}},               # only 1 of 3 tables
            table_names={"users"},
        )
        assert is_fully_empty is False
        status = _derive_status(
            cross_schema_fks=[], invalid_indexes=[], unvalidated=[],
            is_fully_empty=is_fully_empty,
            current_revision_status="no_revision",
            matches_known_baseline=False,
        )
        assert status == "unknown_or_partial_schema"

    def test_5_unknown_revision_refused(self):
        """Criterion 5: unknown revision → unknown_or_partial_schema."""
        is_fully_empty = _compute_is_fully_empty(
            current_revision_status="unknown_revision",
            revisions=["999999999999"],
            inspected={"users": {}},
            table_names={"users", "alembic_version"},
        )
        assert is_fully_empty is False
        status = _derive_status(
            cross_schema_fks=[], invalid_indexes=[], unvalidated=[],
            is_fully_empty=is_fully_empty,
            current_revision_status="unknown_revision",
            matches_known_baseline=False,
        )
        assert status == "unknown_or_partial_schema"

    def test_6a_cross_schema_fk_takes_priority(self):
        """Criterion 6a: cross-schema FK overrides even a matching revision."""
        status = _derive_status(
            cross_schema_fks=[{"source_table": "x", "source_column": "y"}],
            invalid_indexes=[], unvalidated=[],
            is_fully_empty=False,
            current_revision_status="matches",
            matches_known_baseline=True,
        )
        assert status == "cross_schema_fk_present"

    def test_6b_invalid_index_takes_priority(self):
        """Criterion 6b: invalid index overrides empty/revision states."""
        status = _derive_status(
            cross_schema_fks=[],
            invalid_indexes=[{"table": "predictions", "index": "ix", "is_valid": False, "is_ready": True}],
            unvalidated=[],
            is_fully_empty=True,                    # even on empty DB
            current_revision_status="no_revision",
            matches_known_baseline=False,
        )
        assert status == "invalid_indexes_present"

    def test_6c_unvalidated_constraint_takes_priority(self):
        """Criterion 6c: unvalidated constraint overrides empty/revision states."""
        status = _derive_status(
            cross_schema_fks=[], invalid_indexes=[],
            unvalidated=[{"table": "predictions", "constraint": "fk", "kind": "foreign_key"}],
            is_fully_empty=True,
            current_revision_status="matches",
            matches_known_baseline=True,
        )
        assert status == "unvalidated_constraints_present"            