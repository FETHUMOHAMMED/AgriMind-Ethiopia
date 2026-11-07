"""Phase 2 independent-review and adjudication tests."""

from concurrent.futures import ThreadPoolExecutor
import uuid

from fastapi.testclient import TestClient

from app.database import database as db_module
from app.main import app
from app.models.expert_adjudication import ExpertAdjudication
from app.models.expert_review import ExpertReview
from app.models.field_case import FieldCase
from app.models.user import User


client = TestClient(app)


def _register_and_login(name: str):
    email = f"{name.replace(' ', '-').lower()}-{uuid.uuid4().hex}@example.com"
    password = "testpass123"
    registered = client.post(
        "/auth/register",
        json={"full_name": name, "email": email, "password": password},
    )
    assert registered.status_code == 201, registered.text
    logged_in = client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert logged_in.status_code == 200, logged_in.text
    return registered.json()["user_id"], logged_in.json()["access_token"]


def _set_role(user_id: int, role: str):
    db = db_module.SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).one()
        user.role = role
        db.commit()
    finally:
        db.close()


def _create_case():
    _, collector_token = _register_and_login("adjudication collector")
    response = client.post(
        "/field-cases/",
        headers={"Authorization": f"Bearer {collector_token}"},
        json={
            "crop": "wheat",
            "plant_part": "leaf",
            "growth_stage": "vegetative",
            "observed_symptoms": "Lesions on lower leaves",
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
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["case_id"]


def _reviewer(name: str):
    user_id, token = _register_and_login(name)
    _set_role(user_id, "reviewer")
    return user_id, token


def _adjudicator(name: str):
    user_id, token = _register_and_login(name)
    _set_role(user_id, "adjudicator")
    return user_id, token


def _submit_review(case_id: str, token: str, diagnosis: str):
    return client.post(
        "/expert-reviews/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "field_case_id": case_id,
            "status": "verified",
            "verified_diagnosis": diagnosis,
            "verification_method": "independent field inspection",
            "review_notes": "Review recorded independently.",
        },
    )


def _submit_adjudication(case_id: str, token: str, decision: str, diagnosis: str):
    return client.post(
        "/expert-reviews/adjudications/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "field_case_id": case_id,
            "decision": decision,
            "final_diagnosis": diagnosis,
            "taxonomy_version": "agrimind-field-v1",
            "decision_rationale": "Decision recorded after reviewing all submitted opinions.",
        },
    )


def test_two_independent_reviewers_can_review_one_case_and_history_is_preserved():
    case_id = _create_case()
    reviewer_one_id, reviewer_one_token = _reviewer("independent reviewer one")
    reviewer_two_id, reviewer_two_token = _reviewer("independent reviewer two")

    first = _submit_review(case_id, reviewer_one_token, "wheat rust")
    second = _submit_review(case_id, reviewer_two_token, "wheat rust")

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    history = client.get(
        f"/expert-reviews/cases/{case_id}",
        headers={"Authorization": f"Bearer {reviewer_one_token}"},
    )
    assert history.status_code == 200, history.text
    reviews = history.json()["reviews"]
    assert {review["reviewer_user_id"] for review in reviews} == {
        reviewer_one_id,
        reviewer_two_id,
    }
    assert history.json()["adjudication"] is None


def test_same_reviewer_cannot_submit_duplicate_review():
    case_id = _create_case()
    _, reviewer_token = _reviewer("duplicate reviewer")

    first = _submit_review(case_id, reviewer_token, "wheat rust")
    duplicate = _submit_review(case_id, reviewer_token, "wheat rust")

    assert first.status_code == 201, first.text
    assert duplicate.status_code == 409, duplicate.text


def test_farmer_cannot_submit_review_or_adjudication():
    case_id = _create_case()
    _, farmer_token = _register_and_login("ordinary adjudication farmer")

    review = _submit_review(case_id, farmer_token, "wheat rust")
    adjudication = _submit_adjudication(
        case_id, farmer_token, "agreement", "wheat rust"
    )

    assert review.status_code == 403
    assert adjudication.status_code == 403


def test_reviewer_cannot_impersonate_reviewer_and_reviews_are_not_mutable():
    case_id = _create_case()
    reviewer_id, reviewer_token = _reviewer("identity boundary reviewer")
    other_reviewer_id, _ = _reviewer("other identity reviewer")

    impersonation = client.post(
        "/expert-reviews/",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "field_case_id": case_id,
            "reviewer_user_id": other_reviewer_id,
            "status": "verified",
            "verified_diagnosis": "wheat rust",
            "verification_method": "field inspection",
        },
    )
    assert impersonation.status_code == 422

    created = _submit_review(case_id, reviewer_token, "wheat rust")
    assert created.status_code == 201, created.text
    review_id = created.json()["review_id"]

    update = client.put(
        f"/expert-reviews/{review_id}",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={"review_notes": "modified"},
    )
    delete = client.delete(
        f"/expert-reviews/{review_id}",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert update.status_code in {404, 405}
    assert delete.status_code in {404, 405}

    db = db_module.SessionLocal()
    try:
        review = db.query(ExpertReview).filter(ExpertReview.id == review_id).one()
        assert review.reviewer_user_id == reviewer_id
        assert review.review_notes == "Review recorded independently."
    finally:
        db.close()


def test_disagreement_requires_two_different_reviews_and_authorized_adjudicator():
    case_id = _create_case()
    _, reviewer_one_token = _reviewer("disagreement reviewer one")
    _, reviewer_two_token = _reviewer("disagreement reviewer two")
    adjudicator_id, adjudicator_token = _adjudicator("trusted adjudicator")

    assert _submit_review(case_id, reviewer_one_token, "wheat rust").status_code == 201
    assert _submit_review(case_id, reviewer_two_token, "wheat septoria").status_code == 201

    reviewer_attempt = _submit_adjudication(
        case_id, reviewer_one_token, "disagreement", "wheat rust"
    )
    assert reviewer_attempt.status_code == 403

    final = _submit_adjudication(
        case_id, adjudicator_token, "disagreement", "wheat rust"
    )
    assert final.status_code == 201, final.text
    assert final.json()["adjudicator_user_id"] == adjudicator_id
    assert final.json()["decision"] == "disagreement"


def test_agreement_requires_matching_reviews_and_final_decision_is_unique():
    case_id = _create_case()
    _, reviewer_one_token = _reviewer("agreement reviewer one")
    _, reviewer_two_token = _reviewer("agreement reviewer two")
    _, adjudicator_token = _adjudicator("agreement adjudicator")
    _, second_adjudicator_token = _adjudicator("second agreement adjudicator")

    assert _submit_review(case_id, reviewer_one_token, "wheat rust").status_code == 201
    assert _submit_review(case_id, reviewer_two_token, "wheat rust").status_code == 201

    final = _submit_adjudication(
        case_id, adjudicator_token, "agreement", "wheat rust"
    )
    assert final.status_code == 201, final.text

    duplicate_final = _submit_adjudication(
        case_id, second_adjudicator_token, "agreement", "wheat rust"
    )
    assert duplicate_final.status_code == 409, duplicate_final.text

    db = db_module.SessionLocal()
    try:
        assert db.query(ExpertAdjudication).filter(
            ExpertAdjudication.field_case_id
            == db.query(FieldCase).filter(FieldCase.case_id == case_id).one().id
        ).count() == 1
    finally:
        db.close()


def test_concurrent_adjudication_produces_one_final_decision():
    case_id = _create_case()
    _, reviewer_one_token = _reviewer("concurrent reviewer one")
    _, reviewer_two_token = _reviewer("concurrent reviewer two")
    _, adjudicator_one_token = _adjudicator("concurrent adjudicator one")
    _, adjudicator_two_token = _adjudicator("concurrent adjudicator two")

    assert _submit_review(case_id, reviewer_one_token, "wheat rust").status_code == 201
    assert _submit_review(case_id, reviewer_two_token, "wheat rust").status_code == 201

    def submit(token: str):
        local_client = TestClient(app)
        return local_client.post(
            "/expert-reviews/adjudications/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "field_case_id": case_id,
                "decision": "agreement",
                "final_diagnosis": "wheat rust",
                "taxonomy_version": "agrimind-field-v1",
                "decision_rationale": "Concurrent finalization test.",
            },
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(submit, [adjudicator_one_token, adjudicator_two_token])
        )

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 409]

    db = db_module.SessionLocal()
    try:
        case = db.query(FieldCase).filter(FieldCase.case_id == case_id).one()
        assert (
            db.query(ExpertAdjudication)
            .filter(ExpertAdjudication.field_case_id == case.id)
            .count()
            == 1
        )
    finally:
        db.close()


def test_adjudicator_identity_field_is_rejected():
    case_id = _create_case()
    adjudicator_id, adjudicator_token = _adjudicator("adjudicator identity test")

    response = client.post(
        "/expert-reviews/adjudications/",
        headers={"Authorization": f"Bearer {adjudicator_token}"},
        json={
            "field_case_id": case_id,
            "adjudicator_user_id": adjudicator_id + 999,
            "decision": "uncertain",
            "decision_rationale": "Insufficient evidence for a final diagnosis.",
        },
    )
    assert response.status_code == 422
