"""Centralized, read-only policy for ML training-data eligibility."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.expert_adjudication import ExpertAdjudication
from app.models.expert_review import ExpertReview
from app.models.feedback import Feedback
from app.models.field_case import FieldCase
from app.models.prediction import Prediction
from app.routes.predict import UPLOAD_DIR
from app.utils.consent import (
    OBSERVATION_PURPOSE,
    TRAINING_PURPOSE,
    latest_consent,
)
from app.utils.taxonomy import APPROVED_TAXONOMY_VERSION, canonical_diagnosis


ELIGIBILITY_POLICY_VERSION = "training-eligibility-v1"
_REQUIRED_CASE_FIELDS = (
    "crop",
    "plant_part",
    "growth_stage",
    "observed_symptoms",
)


@dataclass(frozen=True)
class EligibilityResult:
    case_id: str
    eligible: bool
    exclusion_reasons: tuple[str, ...]
    missing_provenance: tuple[str, ...]
    canonical_diagnosis: str | None
    consent_status: dict[str, str]
    adjudication_status: str
    image_sha256: str | None
    prediction_id: int | None
    feedback_count: int

    def as_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "eligible": self.eligible,
            "exclusion_reasons": list(self.exclusion_reasons),
            "missing_provenance": list(self.missing_provenance),
            "canonical_diagnosis": self.canonical_diagnosis,
            "consent_status": dict(self.consent_status),
            "adjudication_status": self.adjudication_status,
            "image_sha256": self.image_sha256,
            "prediction_id": self.prediction_id,
            "feedback_count": self.feedback_count,
        }


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _consent_state(
    db: Session,
    case_id: int,
    purpose: str,
    reasons: list[str],
    missing_provenance: list[str],
) -> str:
    record = latest_consent(db, case_id, purpose)
    if record is None:
        _append_unique(reasons, f"missing_{purpose}_consent")
        return "missing"

    if record.status != "granted":
        _append_unique(reasons, f"{purpose}_consent_{record.status}")
    if not record.policy_version or not record.policy_version.strip():
        _append_unique(missing_provenance, f"{purpose}_consent_policy_version")
        _append_unique(reasons, "missing_consent_policy_version")
    return record.status


def _safe_image_path(image_url: str | None) -> Path | None:
    if not image_url:
        return None

    base = Path(UPLOAD_DIR).resolve()
    candidate = Path(image_url)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    candidate = candidate.resolve()
    if base not in candidate.parents or not candidate.is_file():
        return None
    return candidate


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as image_file:
        for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_field_case(db: Session, case: FieldCase) -> EligibilityResult:
    """Evaluate one case without changing database state or exporting data."""
    reasons: list[str] = []
    missing_provenance: list[str] = []
    consent_status = {
        OBSERVATION_PURPOSE: _consent_state(
            db, case.id, OBSERVATION_PURPOSE, reasons, missing_provenance
        ),
        TRAINING_PURPOSE: _consent_state(
            db, case.id, TRAINING_PURPOSE, reasons, missing_provenance
        ),
    }

    for field_name in _REQUIRED_CASE_FIELDS:
        value = getattr(case, field_name, None)
        if not isinstance(value, str) or not value.strip():
            _append_unique(reasons, f"missing_field_{field_name}")

    prediction = None
    if case.prediction_id is None:
        _append_unique(reasons, "missing_evidence")
        _append_unique(missing_provenance, "prediction_id")
    else:
        prediction = (
            db.query(Prediction)
            .filter(Prediction.id == case.prediction_id)
            .first()
        )
        if prediction is None:
            _append_unique(reasons, "missing_prediction_record")
            _append_unique(missing_provenance, "prediction_record")
        else:
            if prediction.user_id != case.collector_user_id:
                _append_unique(reasons, "prediction_collector_mismatch")

            image_path = _safe_image_path(prediction.image_url)
            if image_path is None:
                _append_unique(reasons, "missing_evidence")
                _append_unique(missing_provenance, "stored_original_image")

            if not prediction.image_sha256:
                _append_unique(missing_provenance, "image_sha256")
                _append_unique(reasons, "missing_provenance")
            elif image_path is not None:
                if _file_sha256(image_path) != prediction.image_sha256:
                    _append_unique(reasons, "image_hash_mismatch")

            if not prediction.image_processing_history:
                _append_unique(missing_provenance, "image_processing_history")
                _append_unique(reasons, "missing_provenance")
            else:
                try:
                    processing = json.loads(prediction.image_processing_history)
                except (TypeError, ValueError):
                    processing = None
                if not isinstance(processing, dict) or processing.get(
                    "original_bytes_preserved"
                ) is not True:
                    _append_unique(reasons, "invalid_image_processing_history")

            if not prediction.model_version:
                _append_unique(missing_provenance, "model_version")
                _append_unique(reasons, "missing_provenance")
            if prediction.inference_timestamp is None:
                _append_unique(missing_provenance, "inference_timestamp")
                _append_unique(reasons, "missing_provenance")

    adjudication = (
        db.query(ExpertAdjudication)
        .filter(ExpertAdjudication.field_case_id == case.id)
        .first()
    )
    adjudication_status = adjudication.decision if adjudication else "missing"
    canonical_final_diagnosis = None
    if adjudication is None:
        _append_unique(reasons, "missing_adjudication")
    elif adjudication.decision in {"uncertain", "rejected"}:
        _append_unique(reasons, f"adjudication_{adjudication.decision}")
    elif adjudication.decision not in {"agreement", "disagreement"}:
        _append_unique(reasons, "invalid_adjudication_decision")
    else:
        canonical_final_diagnosis = canonical_diagnosis(
            adjudication.final_diagnosis,
            adjudication.taxonomy_version,
        )
        if adjudication.taxonomy_version != APPROVED_TAXONOMY_VERSION:
            _append_unique(missing_provenance, "approved_taxonomy_version")
            _append_unique(reasons, "invalid_or_missing_taxonomy_version")
        if canonical_final_diagnosis is None:
            _append_unique(reasons, "invalid_diagnosis_taxonomy")

    reviews = (
        db.query(ExpertReview)
        .filter(ExpertReview.field_case_id == case.id)
        .order_by(ExpertReview.created_at.asc(), ExpertReview.id.asc())
        .all()
    )
    if not reviews:
        _append_unique(reasons, "missing_review_history")
    if any(review.status == "pending" for review in reviews):
        _append_unique(reasons, "unresolved_review")

    verified_reviews = [
        review
        for review in reviews
        if review.status == "verified"
        and review.verified_diagnosis
        and review.verified_diagnosis.strip()
        and review.verification_method
        and review.verification_method.strip()
    ]
    review_diagnoses = {
        canonical_diagnosis(
            review.verified_diagnosis,
            adjudication.taxonomy_version if adjudication else None,
        )
        for review in verified_reviews
    }
    if adjudication and adjudication.decision in {"agreement", "disagreement"}:
        if len(verified_reviews) < 2:
            _append_unique(reasons, "insufficient_verified_reviews")
        if None in review_diagnoses:
            _append_unique(reasons, "review_diagnosis_not_in_taxonomy")
        if adjudication.decision == "agreement" and len(review_diagnoses) != 1:
            _append_unique(reasons, "agreement_review_mismatch")
        if adjudication.decision == "disagreement" and len(review_diagnoses) < 2:
            _append_unique(reasons, "disagreement_review_mismatch")
        if (
            canonical_final_diagnosis is not None
            and canonical_final_diagnosis not in review_diagnoses
        ):
            _append_unique(reasons, "final_diagnosis_not_supported_by_reviews")

    feedback_count = 0
    if prediction is not None:
        feedback_count = (
            db.query(Feedback)
            .filter(Feedback.prediction_id == prediction.id)
            .count()
        )
    if feedback_count and adjudication is None:
        _append_unique(reasons, "ordinary_feedback_not_ground_truth")

    return EligibilityResult(
        case_id=case.case_id,
        eligible=not reasons,
        exclusion_reasons=tuple(reasons),
        missing_provenance=tuple(missing_provenance),
        canonical_diagnosis=canonical_final_diagnosis,
        consent_status=consent_status,
        adjudication_status=adjudication_status,
        image_sha256=prediction.image_sha256 if prediction else None,
        prediction_id=prediction.id if prediction else case.prediction_id,
        feedback_count=feedback_count,
    )


def build_training_eligibility_report(
    db: Session,
    evaluated_at: datetime | None = None,
) -> dict:
    """Build an aggregate-only report; this function performs no writes."""
    evaluated_at = evaluated_at or datetime.now(timezone.utc)
    results = [
        evaluate_field_case(db, case)
        for case in db.query(FieldCase)
        .order_by(FieldCase.created_at.asc(), FieldCase.id.asc())
        .all()
    ]

    exclusion_reasons = Counter(
        reason
        for result in results
        if not result.eligible
        for reason in result.exclusion_reasons
    )
    missing_provenance = Counter(
        field_name
        for result in results
        for field_name in result.missing_provenance
    )
    disease_distribution = Counter(
        result.canonical_diagnosis
        for result in results
        if result.eligible and result.canonical_diagnosis
    )
    consent_summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    adjudication_summary = Counter(result.adjudication_status for result in results)
    for result in results:
        for purpose, consent_status in result.consent_status.items():
            consent_summary[purpose][consent_status] += 1

    hashes_to_prediction_ids: dict[str, set[int]] = defaultdict(set)
    for result in results:
        if result.image_sha256 and result.prediction_id is not None:
            hashes_to_prediction_ids[result.image_sha256].add(result.prediction_id)
    duplicate_image_hashes = [
        {"sha256": image_hash, "count": len(prediction_ids)}
        for image_hash, prediction_ids in sorted(hashes_to_prediction_ids.items())
        if len(prediction_ids) > 1
    ]

    eligible_count = sum(result.eligible for result in results)
    excluded_count = len(results) - eligible_count
    return {
        "policy_version": ELIGIBILITY_POLICY_VERSION,
        "evaluated_at": evaluated_at.astimezone(timezone.utc).isoformat(),
        "total_records": len(results),
        "eligible_records": eligible_count,
        "excluded_records": excluded_count,
        "disease_class_distribution": dict(sorted(disease_distribution.items())),
        "exclusion_reasons": dict(sorted(exclusion_reasons.items())),
        "missing_provenance_fields": dict(sorted(missing_provenance.items())),
        "duplicate_image_hashes": duplicate_image_hashes,
        "consent_status_summary": {
            purpose: dict(sorted(statuses.items()))
            for purpose, statuses in sorted(consent_summary.items())
        },
        "adjudication_status_summary": dict(sorted(adjudication_summary.items())),
    }


def training_eligible_cases(db: Session):
    """Return a query of cases passing the complete ML eligibility policy."""
    eligible_ids = [
        case.id
        for case in db.query(FieldCase).order_by(FieldCase.id.asc()).all()
        if evaluate_field_case(db, case).eligible
    ]
    if not eligible_ids:
        return db.query(FieldCase).filter(FieldCase.id == -1)
    return db.query(FieldCase).filter(FieldCase.id.in_(eligible_ids))
