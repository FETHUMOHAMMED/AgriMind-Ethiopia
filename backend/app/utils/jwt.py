from datetime import datetime, timedelta, timezone
import os
from jose import jwt

SUPPORTED_ENVIRONMENTS = frozenset({"development", "test", "production"})
MIN_PRODUCTION_SECRET_LENGTH = 32

_configured_environment = os.getenv("ENVIRONMENT")
if _configured_environment is None or not _configured_environment.strip():
    raise RuntimeError(
        "ENVIRONMENT must be explicitly set to development, test, or production"
    )

ENVIRONMENT = _configured_environment.strip().lower()
if ENVIRONMENT not in SUPPORTED_ENVIRONMENTS:
    raise RuntimeError(
        "Unsupported ENVIRONMENT; expected development, test, or production"
    )

_configured_secret = os.getenv("SECRET_KEY")

if ENVIRONMENT == "production":
    if _configured_secret is None or not _configured_secret.strip():
        raise RuntimeError(
            "SECRET_KEY must be set to a non-empty value when ENVIRONMENT=production"
        )
    if len(_configured_secret) < MIN_PRODUCTION_SECRET_LENGTH:
        raise RuntimeError(
            "SECRET_KEY must be at least 32 characters when ENVIRONMENT=production"
        )
    if len(set(_configured_secret)) < 8:
        raise RuntimeError(
            "SECRET_KEY is too weak when ENVIRONMENT=production"
        )

# A development/test fallback is retained only for these explicitly selected
# non-production environments. Unsupported or production-like values fail
# before this branch is reached.
SECRET_KEY = (
    _configured_secret
    if _configured_secret is not None and _configured_secret.strip()
    else "dev-secret-key"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
