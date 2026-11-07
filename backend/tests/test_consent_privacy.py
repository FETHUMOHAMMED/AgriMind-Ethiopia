"""Phase 3 consent, privacy, and protected-image tests."""

import os
from pathlib import Path
import uuid

from fastapi.testclient import TestClient

from app import main
from app.database import database as db_module
from app.models.consent import ConsentRecord
from app.models.field_case import FieldCase
from app.models.prediction import Prediction
from app.models.user import User
from app.routes import predict as predict_route
from app.utils.consent import training_consent_eligible_cases


client = TestClient(main.app)


def _register_and_login(name: str):
    email = f"{name.replace(' ', '-').lower()}-{uuid.uuid4().hex}@example.com"
    password = "testpass123"
    registered = client.post(
        "/auth/register",
        json={"full_name": name, "email": email, "password": password},
    )
    assert registered.status_code == 201, registered.text
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return registered.json()["user_id"], login.json()["access_token"]


def _set_role(user_id: int, role: str):
    db = db_module.SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.role = role
        db.commit()
    finally:
        db.close()


def _consents(*, expert="granted", training="denied", precise=None):
    result = {
        "observation_collection": {
            "status": "granted",
            "policy_version": "phase3-test-v1",
        },
        "expert_review": {
            "status": expert,
            "policy_version": "phase3-test-v1",
        },
        "ai_training": {
            "status": training,
            "policy_version": "phase3-test-v1",
        },
    }
    if precise is not None:
        result["precise_location"] = {
            "status": precise,
            "policy_version": "phase3-location-v1",
        }
    return result


def _case_payload(**overrides):
    payload = {
        "crop": "wheat",
        "plant_part": "leaf",
        "growth_stage": "vegetative",
        "observed_symptoms": "Yellow lesions on lower leaves",
        "collection_date": "2026-10-31",
        "consent_status": "granted",
        "consents": _consents(),
    }
    payload.update(overrides)
    return payload


def _create_case(token: str, **overrides):
    response = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {token}"},
        json=_case_payload(**overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()["case_id"]


def test_missing_or_denied_collection_consent_is_rejected():
    _, token = _register_and_login("consent collector")

    denied = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {token}"},
        json=_case_payload(consent_status="denied", consents=None),
    )
    assert denied.status_code == 403

    missing_coordinates_consent = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {token}"},
        json=_case_payload(latitude=9.03, longitude=38.74),
    )
    assert missing_coordinates_consent.status_code == 422


def test_request_cannot_bypass_consent_or_identity_controls():
    collector_id, token = _register_and_login("consent identity collector")
    response = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {token}"},
        json=_case_payload(
            collector_user_id=collector_id + 100,
            consent_records=[{"purpose": "ai_training", "status": "granted"}],
        ),
    )
    assert response.status_code == 422


def test_training_consent_is_separate_and_withdrawal_removes_eligibility():
    _, token = _register_and_login("training consent subject")
    case_id = _create_case(token, consents=_consents(training="denied"))

    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.case_id == case_id).one()
        assert training_consent_eligible_cases(db).filter(FieldCase.id == case.id).count() == 0
    finally:
        db.close()

    granted = client.post(
        f"/field-cases/{case_id}/consents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "purpose": "ai_training",
            "status": "granted",
            "policy_version": "phase3-training-v1",
        },
    )
    assert granted.status_code == 201, granted.text

    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.case_id == case_id).one()
        assert training_consent_eligible_cases(db).filter(FieldCase.id == case.id).count() == 1
    finally:
        db.close()

    withdrawn = client.post(
        f"/field-cases/{case_id}/consents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "purpose": "ai_training",
            "status": "withdrawn",
            "policy_version": "phase3-training-v1",
        },
    )
    assert withdrawn.status_code == 201, withdrawn.text

    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.case_id == case_id).one()
        assert training_consent_eligible_cases(db).filter(FieldCase.id == case.id).count() == 0
        events = (
            db.query(ConsentRecord)
            .filter(
                ConsentRecord.field_case_id == case.id,
                ConsentRecord.purpose == "ai_training",
            )
            .order_by(ConsentRecord.id)
            .all()
        )
        assert [event.status for event in events] == ["denied", "granted", "withdrawn"]
    finally:
        db.close()


def test_expert_review_withdrawal_blocks_future_review_but_preserves_audit():
    collector_id, collector_token = _register_and_login("review consent subject")
    case_id = _create_case(collector_token)
    reviewer_id, reviewer_token = _register_and_login("privacy reviewer")
    _set_role(reviewer_id, "reviewer")

    withdrawal = client.post(
        f"/field-cases/{case_id}/consents",
        headers={"Authorization": f"Bearer {collector_token}"},
        json={
            "purpose": "expert_review",
            "status": "withdrawn",
            "policy_version": "phase3-test-v1",
        },
    )
    assert withdrawal.status_code == 201, withdrawal.text

    queue = client.get(
        "/expert-reviews/cases/pending",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert queue.status_code == 200
    assert all(item["case_id"] != case_id for item in queue.json())

    review = client.post(
        "/expert-reviews/",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "field_case_id": case_id,
            "status": "verified",
            "verified_diagnosis": "wheat rust",
            "verification_method": "field inspection",
        },
    )
    assert review.status_code == 403

    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.case_id == case_id).one()
        assert case.collector_user_id == collector_id
        assert db.query(ConsentRecord).filter(
            ConsentRecord.field_case_id == case.id,
            ConsentRecord.purpose == "expert_review",
        ).count() == 2
    finally:
        db.close()


def test_coordinates_are_not_returned_in_ordinary_responses_and_need_adjudicator_access():
    _, collector_token = _register_and_login("coordinate subject")
    case_id = _create_case(
        collector_token,
        latitude=9.03,
        longitude=38.74,
        consents=_consents(precise="granted"),
    )

    owner_response = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {collector_token}"},
        json=_case_payload(),
    )
    assert owner_response.status_code == 201
    assert "latitude" not in owner_response.json()
    assert "longitude" not in owner_response.json()
    assert "collector_user_id" not in owner_response.json()

    reviewer_id, reviewer_token = _register_and_login("coordinate reviewer")
    _set_role(reviewer_id, "reviewer")
    queue = client.get(
        "/expert-reviews/cases/pending",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    queued = next(item for item in queue.json() if item["case_id"] == case_id)
    assert queued["latitude"] is None
    assert queued["longitude"] is None

    farmer_coordinates = client.get(
        f"/expert-reviews/cases/{case_id}/coordinates",
        headers={"Authorization": f"Bearer {collector_token}"},
    )
    assert farmer_coordinates.status_code == 403

    adjudicator_id, adjudicator_token = _register_and_login("coordinate adjudicator")
    _set_role(adjudicator_id, "adjudicator")
    coordinates = client.get(
        f"/expert-reviews/cases/{case_id}/coordinates",
        headers={"Authorization": f"Bearer {adjudicator_token}"},
    )
    assert coordinates.status_code == 200, coordinates.text
    assert coordinates.json() == {
        "case_id": case_id,
        "latitude": 9.03,
        "longitude": 38.74,
    }


def test_prediction_images_are_not_public_and_are_owner_scoped():
    owner_id, owner_token = _register_and_login("image owner")
    _, other_token = _register_and_login("other image user")
    filename = f"privacy-{uuid.uuid4().hex}.png"
    image_path = Path(predict_route.UPLOAD_DIR) / filename
    image_path.write_bytes(b"test image bytes")

    db = db_module.SessionLocal()
    try:
        prediction = Prediction(
            user_id=owner_id,
            image_url=os.path.join(predict_route.UPLOAD_DIR, filename),
            disease="wheat rust",
            confidence=0.9,
            recommendation="inspect crop",
        )
        db.add(prediction)
        db.commit()
    finally:
        db.close()

    public = client.get(f"/uploads/predictions/{filename}")
    assert public.status_code == 401

    owner = client.get(
        f"/uploads/predictions/{filename}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner.status_code == 200
    assert owner.content == b"test image bytes"

    other = client.get(
        f"/uploads/predictions/{filename}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other.status_code == 404
