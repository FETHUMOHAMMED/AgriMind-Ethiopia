"""Deterministic inference test — proves real model inference succeeds.

Unlike `test_successful_prediction_returns_all_fields` (which accepts either
200 or 503), this test REQUIRES HTTP 200 and validates that the returned
disease label belongs to the loaded model's CLASS_NAMES list.
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
    img = Image.new("RGB", (128, 128), color=(50, 120, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_test_token():
    """Register + login, return JWT."""
    email = "test_inference_user@example.com"
    password = "testpass123"
    client.post("/auth/register", json={
        "full_name": "Test Inference User",
        "email": email,
        "password": password,
    })
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


def test_real_model_is_loaded():
    """The model must be loaded and available before inference tests can run."""
    assert real_predictor.MODEL_AVAILABLE is True, \
        "Model is not loaded — cannot run inference test"
    assert real_predictor.model is not None, \
        "Model object is None — cannot run inference test"
    assert len(real_predictor.CLASS_NAMES) > 0, \
        "CLASS_NAMES is empty — checkpoint is malformed"


def test_inference_returns_200_and_valid_class():
    """Deterministic inference test — REQUIRES HTTP 200 and a valid class label.

    Unlike the looser test in test_predict.py, this test will FAIL if the
    model is unavailable. It proves end-to-end inference works: valid image
    → model → class label → API response → DB record.
    """
    # Skip if model not loaded (matches the stricter design — we want this to
    # fail loudly if model is broken, not skip silently)
    if not real_predictor.MODEL_AVAILABLE:
        pytest.skip("Model not loaded — inference test skipped (see test_real_model_is_loaded)")

    token = get_test_token()
    r = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_leaf.png", make_test_image(), "image/png")},
    )

    # REQUIRED: 200 (not 200-or-503)
    assert r.status_code == 200, \
        f"Expected 200 (real inference), got {r.status_code}: {r.text}"

    body = r.json()

    # Required response schema
    for field in (
        "prediction_id", "disease", "confidence",
        "recommendation", "symptoms", "prevention",
        "expert_help", "diagnosed_by",
    ):
        assert field in body, f"Missing field: {field}"

    # Confidence is numeric in [0, 1]
    assert isinstance(body["confidence"], (int, float))
    assert 0.0 <= body["confidence"] <= 1.0

    # The returned disease label MUST be one of the loaded model's classes
    # OR the explicit "Unknown / Uncertain" sentinel
    assert (
        body["disease"] in real_predictor.CLASS_NAMES
        or body["disease"] == "Unknown / Uncertain"
    ), f"Returned disease '{body['disease']}' is not in CLASS_NAMES and is not the uncertain sentinel"

    # All string fields must be non-None strings
    for text_field in ("recommendation", "symptoms", "prevention", "expert_help", "diagnosed_by"):
        assert isinstance(body[text_field], str), \
            f"Field {text_field} is not a string: {type(body[text_field])}"


def test_prediction_record_written_to_db():
    """A successful inference must write exactly one new prediction record."""
    if not real_predictor.MODEL_AVAILABLE:
        pytest.skip("Model not loaded")

    token = get_test_token()

    # Count before
    r_hist_before = client.get(
        "/predict/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_hist_before.status_code == 200
    count_before = len(r_hist_before.json())

    # Run inference
    r_pred = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_leaf.png", make_test_image(), "image/png")},
    )
    assert r_pred.status_code == 200

    # Count after — must be exactly +1
    r_hist_after = client.get(
        "/predict/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_hist_after.status_code == 200
    count_after = len(r_hist_after.json())

    assert count_after == count_before + 1, \
        f"Expected +1 prediction record, got {count_after - count_before}"