"""
AgriMind Ethiopia — Prediction Endpoint Regression Tests
Run: pytest backend/tests/ -v
"""
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.ai import real_predictor

client = TestClient(app)


def make_test_image():
    """Create a small valid PNG image in memory."""
    img = Image.new("RGB", (100, 100), color=(0, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_test_token():
    """Register + login, return JWT."""
    email = "test_predict_user@example.com"
    password = "testpass123"

    client.post("/auth/register", json={
        "full_name": "Test Predict User",
        "email": email,
        "password": password,
    })

    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


# FIX 11.1: Unauthorized → 401
def test_unauthorized_returns_401():
    r = client.post("/predict/", files={"file": ("x.jpg", b"data", "image/jpeg")})
    assert r.status_code == 401


# FIX 11.2: Invalid image bytes → 400
def test_invalid_image_returns_400():
    token = get_test_token()
    r = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fake.jpg", b"not an image", "image/jpeg")},
    )
    assert r.status_code == 400
    assert "Invalid image" in r.json()["detail"]


# FIX 11.3: Unsupported extension → 400
def test_unsupported_extension_returns_400():
    token = get_test_token()
    r = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert r.status_code == 400
    assert "not allowed" in r.json()["detail"]


# FIX 11.4: Model unavailable → 503 (NOT a fabricated diagnosis)
def test_model_unavailable_returns_503(monkeypatch):
    monkeypatch.setattr(real_predictor, "MODEL_AVAILABLE", False)
    token = get_test_token()
    r = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("leaf.png", make_test_image(), "image/png")},
    )
    assert r.status_code == 503
    assert "unavailable" in r.json()["detail"].lower()


# FIX 11.5: Successful prediction returns all 7 expected fields
def test_successful_prediction_returns_all_fields():
    token = get_test_token()
    r = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("leaf.png", make_test_image(), "image/png")},
    )
    if r.status_code == 200:
        body = r.json()
        for field in (
            "prediction_id", "disease", "confidence",
            "recommendation", "symptoms", "prevention",
            "expert_help", "diagnosed_by",
        ):
            assert field in body, f"Missing field: {field}"
        assert isinstance(body["confidence"], (int, float))
    else:
        assert r.status_code == 503


# FIX 11.6: Feedback for non-existent prediction → 404
def test_feedback_nonexistent_prediction_returns_404():
    token = get_test_token()
    r = client.post(
        "/feedback/",
        headers={"Authorization": f"Bearer {token}"},
        json={"prediction_id": 999999, "correct": True, "comment": "test"},
    )
    assert r.status_code == 404


# FIX 11.7: Failed prediction does NOT create a DB record
def test_failed_prediction_does_not_create_db_row(monkeypatch):
    monkeypatch.setattr(real_predictor, "MODEL_AVAILABLE", False)
    token = get_test_token()

    r_before = client.get(
        "/predict/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    count_before = len(r_before.json())

    client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("leaf.png", make_test_image(), "image/png")},
    )

    r_after = client.get(
        "/predict/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(r_after.json()) == count_before
    
    

# FIX B: Cross-user feedback boundary → 404
def test_feedback_other_users_prediction_returns_404():
    """
    User A creates a prediction.
    User B attempts to submit feedback for User A's prediction.
    Expectation: 404 (prediction not visible to user B).
    """
    # --- Step 1: Create User A and get a prediction ---
    email_a = "user_a_feedback@example.com"
    password_a = "testpassA123"

    client.post("/auth/register", json={
        "full_name": "User A",
        "email": email_a,
        "password": password_a,
    })
    r_login_a = client.post("/auth/login", json={
        "email": email_a,
        "password": password_a,
    })
    assert r_login_a.status_code == 200
    token_a = r_login_a.json()["access_token"]

    # Get count before for user A
    r_hist_a_before = client.get(
        "/predict/history",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    count_a_before = len(r_hist_a_before.json())

    # User A submits a prediction
    r_pred = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("leaf.png", make_test_image(), "image/png")},
    )

    if r_pred.status_code != 200:
        # If model unavailable, skip this test gracefully
        # (prediction IDs cannot be tested without a real prediction)
        pytest.skip("Model unavailable — cannot create prediction for ownership test")

    prediction_a_id = r_pred.json()["prediction_id"]

    # --- Step 2: Create User B ---
    email_b = "user_b_feedback@example.com"
    password_b = "testpassB123"

    client.post("/auth/register", json={
        "full_name": "User B",
        "email": email_b,
        "password": password_b,
    })
    r_login_b = client.post("/auth/login", json={
        "email": email_b,
        "password": password_b,
    })
    assert r_login_b.status_code == 200
    token_b = r_login_b.json()["access_token"]

    # --- Step 3: User B tries to submit feedback on User A's prediction ---
    r_feedback = client.post(
        "/feedback/",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "prediction_id": prediction_a_id,
            "correct": True,
            "comment": "cross-user attempt",
        },
    )

    # --- Step 4: Assertions ---
    assert r_feedback.status_code == 404, \
        f"Expected 404 for cross-user feedback, got {r_feedback.status_code}: {r_feedback.text}"
    assert "not found" in r_feedback.json()["detail"].lower()

    # --- Step 5: Verify User B's feedback history is empty ---
    r_hist_b = client.get(
        "/feedback/",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r_hist_b.status_code == 200
    assert len(r_hist_b.json()) == 0, \
        "User B should have zero feedback records after cross-user attempt"

    # --- Step 6: Verify User A's feedback history is also empty ---
    # (no legitimate feedback was submitted either)
    r_hist_a = client.get(
        "/feedback/",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r_hist_a.status_code == 200
    assert len(r_hist_a.json()) == 0, \
        "No feedback should exist because cross-user attempt was blocked"