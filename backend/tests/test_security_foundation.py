"""Phase 1 security-foundation tests."""

import os
import subprocess
import sys
import uuid

from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.models.user import User
from app.utils.jwt import ALGORITHM, SECRET_KEY
from app.database import database as db_module


client = TestClient(app)


def _run_jwt_subprocess(*, environment: str | None, secret: str | None):
    child_environment = os.environ.copy()
    if environment is None:
        child_environment.pop("ENVIRONMENT", None)
    else:
        child_environment["ENVIRONMENT"] = environment
    if secret is None:
        child_environment.pop("SECRET_KEY", None)
    else:
        child_environment["SECRET_KEY"] = secret

    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.utils.jwt import create_access_token; "
            "assert create_access_token({'sub': '1'})",
        ],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=child_environment,
        capture_output=True,
        text=True,
    )


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


def test_production_without_secret_key_fails_closed():
    result = _run_jwt_subprocess(environment="production", secret=None)

    assert result.returncode != 0
    assert "SECRET_KEY must be set" in result.stderr
    assert "dev-secret-key" not in result.stdout + result.stderr


def test_production_empty_secret_key_fails_closed():
    result = _run_jwt_subprocess(environment="production", secret="   ")

    assert result.returncode != 0
    assert "SECRET_KEY must be set" in result.stderr


def test_production_weak_secret_key_fails_closed():
    result = _run_jwt_subprocess(environment="production", secret="x" * 64)

    assert result.returncode != 0
    assert "SECRET_KEY is too weak" in result.stderr


def test_misspelled_environment_fails_closed():
    result = _run_jwt_subprocess(
        environment="prodution",
        secret="a-strong-production-secret-with-more-than-32-chars-1234",
    )

    assert result.returncode != 0
    assert "Unsupported ENVIRONMENT" in result.stderr


def test_unset_environment_fails_closed():
    result = _run_jwt_subprocess(environment=None, secret=None)

    assert result.returncode != 0
    assert "ENVIRONMENT must be explicitly set" in result.stderr


def test_valid_production_configuration_works_without_exposing_secret():
    secret = "strong-production-secret-with-32-plus-characters-123456"
    result = _run_jwt_subprocess(environment="production", secret=secret)

    assert result.returncode == 0, result.stderr
    assert secret not in result.stdout + result.stderr


def test_development_and_test_configurations_remain_compatible():
    for environment in ("development", "test"):
        result = _run_jwt_subprocess(environment=environment, secret=None)
        assert result.returncode == 0, (environment, result.stderr)


def test_forged_jwt_role_claim_does_not_grant_reviewer_access():
    user_id, _ = _register_and_login("role-claim farmer")
    forged_token = jwt.encode(
        {"sub": str(user_id), "role": "reviewer"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/expert-reviews/cases/pending",
        headers={"Authorization": f"Bearer {forged_token}"},
    )

    assert response.status_code == 403


def test_registration_rejects_requested_reviewer_role_and_defaults_to_farmer():
    email = f"registration-role-{uuid.uuid4().hex}@example.com"
    rejected = client.post(
        "/auth/register",
        json={
            "full_name": "Requested reviewer",
            "email": email,
            "password": "testpass123",
            "role": "reviewer",
        },
    )
    assert rejected.status_code == 422

    registered = client.post(
        "/auth/register",
        json={
            "full_name": "Normal farmer",
            "email": email,
            "password": "testpass123",
        },
    )
    assert registered.status_code == 201, registered.text

    db = db_module.SessionLocal()
    try:
        user = db.query(User).filter(User.id == registered.json()["user_id"]).one()
        assert user.role == "farmer"
    finally:
        db.close()
