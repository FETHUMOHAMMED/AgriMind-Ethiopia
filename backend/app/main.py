import os

from fastapi import FastAPI
from app.utils import jwt  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import engine
from app.database.schema_state import validate_application_schema
from app.models import (
    user,
    prediction,
    feedback,
    field_case,
    consent,
    expert_review,
    expert_adjudication,
)
from app.routes import (
    auth,
    predict,
    users,
    feedback,
    language,
    field_cases,
    expert_reviews,
    uploads,
    training_eligibility,
)

# Schema changes are applied only through an explicit migration procedure.
# Tests create their disposable schema before importing this module and set the
# explicit test bypass in backend/tests/conftest.py.
_explicit_test_mode = (
    os.getenv("ENVIRONMENT", "").strip().lower() == "test"
    and os.getenv("AGRIMIND_TESTING") == "1"
)
if not _explicit_test_mode:
    validate_application_schema(engine)

app = FastAPI(
    title="AgriMind Ethiopia API",
    version="1.0.0",
    description="AI-powered agriculture assistant for Ethiopian farmers",
)

# Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(users.router)
app.include_router(feedback.router)
app.include_router(language.router)
app.include_router(field_cases.router)
app.include_router(expert_reviews.router)
app.include_router(uploads.router)
app.include_router(training_eligibility.router)

@app.get("/")
def root():
    return {"message": "AgriMind Ethiopia API is running"}
