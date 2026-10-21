"""V2 API integration test — temporary model swap for the live endpoint.

Verifies v2 works through the real FastAPI prediction endpoint without
permanently changing real_predictor.py or the live application. Uses a
pytest fixture to swap real_predictor's module globals to v2 during the
test, then restores the original v1 model.

IMPORTANT: This test modifies module-global state (real_predictor.model,
CLASS_NAMES, MODEL_AVAILABLE). Do NOT run with pytest-xdist (parallel)
or pytest-forked — the swap would affect other tests running concurrently.
"""
import io
from pathlib import Path

import pytest
import torch
import torch.nn as nn
from fastapi.testclient import TestClient
from PIL import Image
from torchvision import models

from app.main import app
from app.ai import real_predictor

client = TestClient(app)

V2_PATH = Path(real_predictor.__file__).parent / "model" / "agrimind_mobilenetv2_v2.pth"


def make_test_image():
    img = Image.new("RGB", (128, 128), color=(50, 120, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_test_token():
    email = "test_v2_integration@example.com"
    password = "testpass123"
    client.post("/auth/register", json={
        "full_name": "Test V2 Integration",
        "email": email,
        "password": password,
    })
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture
def with_v2_model():
    """Temporarily patch real_predictor to use v2, then restore v1."""
    if not V2_PATH.exists():
        pytest.skip(f"v2 checkpoint not found: {V2_PATH}")

    # Save original v1 state
    orig_model = real_predictor.model
    orig_classes = real_predictor.CLASS_NAMES
    orig_available = real_predictor.MODEL_AVAILABLE

    # Load v2
    ckpt = torch.load(V2_PATH, map_location="cpu", weights_only=True)
    v2_classes = ckpt["classes"]

    v2_model = models.mobilenet_v2(weights=None)
    v2_model.classifier[1] = nn.Linear(v2_model.last_channel, len(v2_classes))
    v2_model.load_state_dict(ckpt["model_state"], strict=True)
    v2_model.eval()

    # Patch module globals
    real_predictor.model = v2_model
    real_predictor.CLASS_NAMES = v2_classes
    real_predictor.MODEL_AVAILABLE = True

    try:
        yield v2_classes
    finally:
        # Restore v1
        real_predictor.model = orig_model
        real_predictor.CLASS_NAMES = orig_classes
        real_predictor.MODEL_AVAILABLE = orig_available


def test_v2_predicts_through_api(with_v2_model):
    """V2 inference works through the live FastAPI endpoint."""
    v2_classes = with_v2_model
    assert len(v2_classes) == 15, f"Expected 15 v2 classes, got {len(v2_classes)}"

    token = get_test_token()
    r = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.png", make_test_image(), "image/png")},
    )

    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    body = r.json()

    # All 8 response fields present
    for field in (
        "prediction_id", "disease", "confidence",
        "recommendation", "symptoms", "prevention",
        "expert_help", "diagnosed_by",
    ):
        assert field in body, f"Missing field: {field}"

    # Disease is a valid v2 class (or the explicit uncertain sentinel)
    assert (
        body["disease"] in v2_classes
        or body["disease"] == "Unknown / Uncertain"
    ), f"Disease '{body['disease']}' not in v2 classes and not uncertain"

    # Confidence in [0, 1]
    assert isinstance(body["confidence"], (int, float))
    assert 0.0 <= body["confidence"] <= 1.0

    # Text fields are strings
    for f in ("recommendation", "symptoms", "prevention", "expert_help", "diagnosed_by"):
        assert isinstance(body[f], str)

    # If not uncertain, the recommendation must NOT be the DEFAULT_REC fallback
    if body["disease"] != "Unknown / Uncertain":
        rec = real_predictor.get_recommendation(body["disease"])
        assert rec is not real_predictor.DEFAULT_REC, \
            f"v2 class {body['disease']} fell back to DEFAULT_REC — missing recommendation"


def test_v2_record_written_to_db(with_v2_model):
    """V2 inference writes exactly one prediction record to the isolated test DB."""
    token = get_test_token()

    r_before = client.get("/predict/history", headers={"Authorization": f"Bearer {token}"})
    assert r_before.status_code == 200
    count_before = len(r_before.json())

    r = client.post(
        "/predict/",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.png", make_test_image(), "image/png")},
    )
    assert r.status_code == 200

    r_after = client.get("/predict/history", headers={"Authorization": f"Bearer {token}"})
    assert r_after.status_code == 200
    assert len(r_after.json()) == count_before + 1, \
        f"Expected +1 record, got {len(r_after.json()) - count_before}"


def test_v1_restored_after_v2_tests():
    """Sanity check: after the v2 fixture tests complete, v1 must be restored."""
    assert real_predictor.MODEL_AVAILABLE is True, "v1 should be available"
    assert real_predictor.model is not None, "v1 model should be loaded"
    assert len(real_predictor.CLASS_NAMES) == 19, \
        f"Expected 19 v1 classes, got {len(real_predictor.CLASS_NAMES)}"