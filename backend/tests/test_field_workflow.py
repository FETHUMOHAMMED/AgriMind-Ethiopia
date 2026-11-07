"""Tests for field-case collection and expert verification boundaries."""

import os
import subprocess
import sys
import uuid

from fastapi.testclient import TestClient

from app.database import database as db_module
from app.main import app
from app.models.expert_review import ExpertReview
from app.models.field_case import FieldCase
from app.models.user import User


client = TestClient(app)


def _register_and_login(name: str):
    email = f"{name.replace(' ', '-').lower()}-{uuid.uuid4().hex}@example.com"
    password = "testpass123"
    response = client.post(
        "/auth/register",
        json={"full_name": name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    login = client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text
    return response.json()["user_id"], login.json()["access_token"]


def _set_role(user_id: int, role: str):
    db = db_module.SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.role = role
        db.commit()
    finally:
        db.close()


def _field_case_payload(**overrides):
    payload = {
        "crop": "wheat",
        "plant_part": "leaf",
        "growth_stage": "vegetative",
        "observed_symptoms": "Yellow lesions on lower leaves",
        "collection_date": "2026-10-31",
        "consent_status": "granted",
        "consents": {
            "observation_collection": {
                "status": "granted",
                "policy_version": "phase3-test-v1",
            },
            "expert_review": {
                "status": "granted",
                "policy_version": "phase3-test-v1",
            },
            "ai_training": {
                "status": "denied",
                "policy_version": "phase3-test-v1",
            },
        },
    }
    payload.update(overrides)
    return payload


def test_unauthenticated_field_case_request_is_rejected():
    response = client.post("/field-cases/", json=_field_case_payload())
    assert response.status_code == 401


def test_field_case_does_not_require_prediction_and_rejects_impersonation_id():
    collector_id, token = _register_and_login("field collector")
    response = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {token}"},
        json=_field_case_payload(
            latitude=9.03,
            longitude=38.74,
            consents={
                "observation_collection": {
                    "status": "granted",
                    "policy_version": "phase3-test-v1",
                },
                "expert_review": {
                    "status": "granted",
                    "policy_version": "phase3-test-v1",
                },
                "ai_training": {
                    "status": "denied",
                    "policy_version": "phase3-test-v1",
                },
                "precise_location": {
                    "status": "granted",
                    "policy_version": "phase3-location-v1",
                },
            },
        ),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["prediction_id"] is None
    assert "latitude" not in body
    assert "longitude" not in body

    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.case_id == body["case_id"]).one()
        assert case.collector_user_id == collector_id
        assert case.prediction_id is None
        assert case.latitude == 9.03
        assert case.longitude == 38.74
    finally:
        db.close()

    impersonation_response = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {token}"},
        json=_field_case_payload(collector_user_id=collector_id + 9999),
    )
    assert impersonation_response.status_code == 422


def test_farmer_cannot_access_reviewer_routes_or_submit_review():
    _, farmer_token = _register_and_login("ordinary farmer")
    headers = {"Authorization": f"Bearer {farmer_token}"}

    queue_response = client.get("/expert-reviews/cases/pending", headers=headers)
    assert queue_response.status_code == 403

    review_response = client.post(
        "/expert-reviews/",
        headers=headers,
        json={
            "field_case_id": "FC-does-not-exist",
            "status": "verified",
            "verified_diagnosis": "wheat rust",
            "verification_method": "field inspection",
        },
    )
    assert review_response.status_code == 403


def test_reviewer_can_retrieve_case_submit_review_and_persist_it():
    collector_id, collector_token = _register_and_login("reviewed collector")
    case_response = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {collector_token}"},
        json=_field_case_payload(variety="Danda", region="Oromia"),
    )
    assert case_response.status_code == 201, case_response.text
    case_id = case_response.json()["case_id"]

    reviewer_id, reviewer_token = _register_and_login("trusted reviewer")
    _set_role(reviewer_id, "reviewer")
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    queue_response = client.get(
        "/expert-reviews/cases/pending", headers=reviewer_headers
    )
    assert queue_response.status_code == 200, queue_response.text
    queued_case = next(item for item in queue_response.json() if item["case_id"] == case_id)
    assert queued_case["variety"] == "Danda"

    submit_response = client.post(
        "/expert-reviews/",
        headers=reviewer_headers,
        json={
            "field_case_id": case_id,
            "status": "verified",
            "verified_diagnosis": "wheat rust",
            "verification_method": "expert field inspection",
            "review_notes": "Symptoms and lesion pattern match.",
        },
    )
    assert submit_response.status_code == 201, submit_response.text
    assert submit_response.json()["status"] == "verified"

    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.case_id == case_id).one()
        review = db.query(ExpertReview).filter(ExpertReview.field_case_id == case.id).one()
        assert review.reviewer_user_id == reviewer_id
        assert review.status == "verified"
        assert review.verified_diagnosis == "wheat rust"
        assert review.reviewed_at is not None
        assert review.created_at is not None
    finally:
        db.close()

    queue_after = client.get(
        "/expert-reviews/cases/pending", headers=reviewer_headers
    )
    assert queue_after.status_code == 200
    queued_after_review = next(
        item for item in queue_after.json() if item["case_id"] == case_id
    )
    assert queued_after_review["review_count"] == 1


def test_invalid_review_status_and_missing_verification_fields_are_rejected():
    reviewer_id, reviewer_token = _register_and_login("validation reviewer")
    _set_role(reviewer_id, "reviewer")
    headers = {"Authorization": f"Bearer {reviewer_token}"}

    invalid_status = client.post(
        "/expert-reviews/",
        headers=headers,
        json={"field_case_id": "FC-missing", "status": "confirmed"},
    )
    assert invalid_status.status_code == 422

    missing_verified_fields = client.post(
        "/expert-reviews/",
        headers=headers,
        json={"field_case_id": "FC-missing", "status": "verified"},
    )
    assert missing_verified_fields.status_code == 422


def test_production_without_secret_key_fails_in_isolated_process():
    environment = os.environ.copy()
    environment.pop("SECRET_KEY", None)
    environment["ENVIRONMENT"] = "production"
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "SECRET_KEY must be set to a non-empty value" in (
        result.stdout + result.stderr
    )


def test_nonproduction_jwt_configuration_remains_compatible():
    environment = os.environ.copy()
    environment.pop("SECRET_KEY", None)
    environment["ENVIRONMENT"] = "test"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.utils.jwt import create_access_token; assert create_access_token({'sub': '1'})",
        ],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
