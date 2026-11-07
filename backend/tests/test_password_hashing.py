"""Isolated regression tests for the bcrypt password format."""

import bcrypt

from app.utils.security import hash_password, verify_password


def test_password_hash_round_trip_uses_standard_bcrypt_format():
    hashed = hash_password("testpass123")

    assert hashed.startswith(("$2a$", "$2b$", "$2y$"))
    assert verify_password("testpass123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_existing_bcrypt_hashes_remain_verifiable():
    existing_format_hash = bcrypt.hashpw(b"legacy-password", bcrypt.gensalt()).decode("ascii")

    assert verify_password("legacy-password", existing_format_hash)
