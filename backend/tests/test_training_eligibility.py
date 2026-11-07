"""Phase 4 training-data eligibility and provenance tests."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.database import database as db_module
from app.models.consent import ConsentRecord
from app.models.expert_adjudication import ExpertAdjudication
from app.models.expert_review import ExpertReview
from app.models.feedback import Feedback
from app.models.field_case import FieldCase
from app.models.prediction import Prediction
from app.models.user import User
from app.routes import predict as predict_route
from app.utils.taxonomy import APPROVED_TAXONOMY_VERSION
from app.utils.training_eligibility import (
    build_training_eligibility_report,
    evaluate_field_case,
)


client = TestClient(app)


def _user(role="farmer"):
    db = db_module.SessionLocal()
    try:
        user = User(
            full_name=f"Phase 4 {role}",
            email=f"phase4-{role}-{uuid.uuid4().hex}@example.com",
            password_hash="test-hash",
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def _register_and_login(name):
    email = f"phase4-api-{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/auth/register",
        json={"full_name": name, "email": email, "password": "testpass123"},
    )
    assert response.status_code == 201, response.text
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "testpass123"},
    )
    assert login.status_code == 200, login.text
    return response.json()["user_id"], login.json()["access_token"]


def _prediction(
    user_id,
    *,
    with_provenance=True,
    image_hash=None,
    image_bytes=b"phase4-original-image-bytes",
):
    filename = f"phase4-{uuid.uuid4().hex}.png"
    image_path = Path(predict_route.UPLOAD_DIR) / filename
    image_path.write_bytes(image_bytes)
    digest = image_hash or hashlib.sha256(image_bytes).hexdigest()

    values = {
        "user_id": user_id,
        "image_url": str(image_path),
        "disease": "wheat rust",
        "confidence": 0.91,
        "recommendation": "inspect crop",
    }
    if with_provenance:
        values.update(
            {
                "image_sha256": digest,
                "image_processing_history": json.dumps(
                    {
                        "schema_version": 1,
                        "operations": [],
                        "original_bytes_preserved": True,
                    }
                ),
                "model_version": "test-model-v1",
                "inference_timestamp": datetime.now(timezone.utc),
            }
        )

    db = db_module.SessionLocal()
    try:
        prediction = Prediction(**values)
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        return prediction.id
    finally:
        db.close()


def _case(
    user_id,
    *,
    prediction_id=None,
    training_status="granted",
    include_training_consent=True,
    precise=False,
):
    db = db_module.SessionLocal()
    try:
        case = FieldCase(
            case_id=f"FC-{uuid.uuid4()}",
            collector_user_id=user_id,
            prediction_id=prediction_id,
            crop="wheat",
            plant_part="leaf",
            growth_stage="vegetative",
            observed_symptoms="Yellow lesions on lower leaves",
            region="Oromia",
            collection_date=datetime.now(timezone.utc).date(),
            consent_status="granted",
            latitude=9.03 if precise else None,
            longitude=38.74 if precise else None,
        )
        db.add(case)
        db.flush()
        now = datetime.now(timezone.utc)
        consents = [
            ("observation_collection", "granted", "phase4-observation-v1"),
            ("expert_review", "granted", "phase4-review-v1"),
        ]
        if include_training_consent:
            consents.append(("ai_training", training_status, "phase4-training-v1"))
        if precise:
            consents.append(("precise_location", "granted", "phase4-location-v1"))
        for purpose, status, policy_version in consents:
            db.add(
                ConsentRecord(
                    field_case_id=case.id,
                    subject_user_id=user_id,
                    purpose=purpose,
                    status=status,
                    policy_version=policy_version,
                    recorded_at=now,
                )
            )
        db.commit()
        db.refresh(case)
        return case.id
    finally:
        db.close()


def _reviews_and_adjudication(
    case_id,
    *,
    decision="agreement",
    final_diagnosis="wheat rust",
    taxonomy_version=APPROVED_TAXONOMY_VERSION,
    diagnoses=("wheat rust", "wheat rust"),
):
    db = db_module.SessionLocal()
    try:
        reviewer_ids = [_user("reviewer"), _user("reviewer")]
        adjudicator_id = _user("adjudicator")
        for reviewer_id, diagnosis in zip(reviewer_ids, diagnoses):
            db.add(
                ExpertReview(
                    field_case_id=case_id,
                    reviewer_user_id=reviewer_id,
                    status="verified",
                    verified_diagnosis=diagnosis,
                    verification_method="independent inspection",
                    review_notes="Phase 4 test review",
                    reviewed_at=datetime.now(timezone.utc),
                )
            )
        db.flush()
        db.add(
            ExpertAdjudication(
                field_case_id=case_id,
                adjudicator_user_id=adjudicator_id,
                decision=decision,
                final_diagnosis=final_diagnosis,
                taxonomy_version=taxonomy_version,
                decision_rationale="Phase 4 test adjudication",
                decided_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    finally:
        db.close()


def _evaluate(case_id):
    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.id == case_id).one()
        return evaluate_field_case(db, case)
    finally:
        db.close()


def test_only_consented_complete_adjudicated_case_is_eligible():
    user_id = _user()
    prediction_id = _prediction(user_id)
    case_id = _case(user_id, prediction_id=prediction_id)
    _reviews_and_adjudication(case_id)

    result = _evaluate(case_id)
    assert result.eligible is True
    assert result.canonical_diagnosis == "wheat_rust"
    assert result.exclusion_reasons == ()


def test_missing_and_withdrawn_training_consent_are_excluded():
    user_id = _user()
    missing_case = _case(user_id, prediction_id=_prediction(user_id), include_training_consent=False)
    _reviews_and_adjudication(missing_case)
    assert "missing_ai_training_consent" in _evaluate(missing_case).exclusion_reasons

    withdrawn_case = _case(user_id, prediction_id=_prediction(user_id))
    _reviews_and_adjudication(withdrawn_case)
    db = db_module.SessionLocal()
    try:
        db.add(
            ConsentRecord(
                field_case_id=withdrawn_case,
                subject_user_id=user_id,
                purpose="ai_training",
                status="withdrawn",
                policy_version="phase4-training-v1",
                recorded_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    finally:
        db.close()
    assert "ai_training_consent_withdrawn" in _evaluate(withdrawn_case).exclusion_reasons


def test_uncertain_and_rejected_adjudications_are_never_eligible():
    for decision in ("uncertain", "rejected"):
        user_id = _user()
        case_id = _case(user_id, prediction_id=_prediction(user_id))
        _reviews_and_adjudication(
            case_id,
            decision=decision,
            final_diagnosis=None,
            taxonomy_version=None,
            diagnoses=("wheat rust", "wheat rust"),
        )
        result = _evaluate(case_id)
        assert result.eligible is False
        assert f"adjudication_{decision}" in result.exclusion_reasons


def test_invalid_taxonomy_and_legacy_prediction_provenance_are_excluded():
    user_id = _user()
    legacy_prediction = _prediction(user_id, with_provenance=False)
    legacy_case = _case(user_id, prediction_id=legacy_prediction)
    _reviews_and_adjudication(
        legacy_case,
        final_diagnosis="not-an-approved-disease",
        taxonomy_version=APPROVED_TAXONOMY_VERSION,
    )
    result = _evaluate(legacy_case)
    assert result.eligible is False
    assert "invalid_diagnosis_taxonomy" in result.exclusion_reasons
    assert "image_sha256" in result.missing_provenance
    assert "model_version" in result.missing_provenance
    assert "inference_timestamp" in result.missing_provenance


def test_missing_evidence_and_farmer_feedback_never_create_ground_truth():
    user_id = _user()
    no_evidence_case = _case(user_id, prediction_id=None)
    _reviews_and_adjudication(no_evidence_case)
    result = _evaluate(no_evidence_case)
    assert result.eligible is False
    assert "missing_evidence" in result.exclusion_reasons

    feedback_prediction = _prediction(user_id)
    feedback_case = _case(user_id, prediction_id=feedback_prediction)
    db = db_module.SessionLocal()
    try:
        db.add(
            Feedback(
                user_id=user_id,
                prediction_id=feedback_prediction,
                correct=True,
                comment="farmer agrees",
            )
        )
        db.commit()
    finally:
        db.close()
    feedback_result = _evaluate(feedback_case)
    assert feedback_result.eligible is False
    assert "missing_adjudication" in feedback_result.exclusion_reasons
    assert "ordinary_feedback_not_ground_truth" in feedback_result.exclusion_reasons


def test_duplicate_hashes_and_report_counts_are_aggregate_and_consistent():
    user_id = _user()
    duplicate_bytes = b"phase4-duplicate-image-bytes"
    duplicate_hash = hashlib.sha256(duplicate_bytes).hexdigest()
    first_prediction = _prediction(
        user_id,
        image_hash=duplicate_hash,
        image_bytes=duplicate_bytes,
    )
    second_prediction = _prediction(
        user_id,
        image_hash=duplicate_hash,
        image_bytes=duplicate_bytes,
    )
    first_case = _case(user_id, prediction_id=first_prediction)
    second_case = _case(user_id, prediction_id=second_prediction)
    _reviews_and_adjudication(first_case)
    _reviews_and_adjudication(second_case)

    db = db_module.SessionLocal()
    try:
        report = build_training_eligibility_report(
            db,
            evaluated_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        )
    finally:
        db.close()

    assert report["total_records"] == (
        report["eligible_records"] + report["excluded_records"]
    )
    assert any(
        item["sha256"] == duplicate_hash and item["count"] == 2
        for item in report["duplicate_image_hashes"]
    )
    report_text = json.dumps(report)
    assert "collector_user_id" not in report_text
    assert "latitude" not in report_text
    assert "longitude" not in report_text
    assert "phase4-" not in report_text


def test_report_endpoint_is_protected_and_aggregate_only():
    farmer_id, farmer_token = _register_and_login("report farmer")
    farmer_response = client.get(
        "/training-eligibility/report",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert farmer_response.status_code == 403

    db = db_module.SessionLocal()
    try:
        user = db.query(User).filter(User.id == farmer_id).one()
        user.role = "adjudicator"
        db.commit()
    finally:
        db.close()

    report_response = client.get(
        "/training-eligibility/report",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert report_response.status_code == 200, report_response.text
    report_text = json.dumps(report_response.json())
    assert "collector_user_id" not in report_text
    assert "latitude" not in report_text
    assert "longitude" not in report_text
