from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database.database import Base


class ExpertReview(Base):
    __tablename__ = "expert_reviews"

    id = Column(Integer, primary_key=True, index=True)
    field_case_id = Column(Integer, ForeignKey("field_cases.id"), nullable=False, index=True)
    reviewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    verified_diagnosis = Column(String(200), nullable=True)
    verification_method = Column(String(200), nullable=True)
    review_notes = Column(String(4000), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "field_case_id",
            "reviewer_user_id",
            name="uq_expert_reviews_case_reviewer",
        ),
        CheckConstraint(
            "status IN ('pending', 'verified', 'uncertain', 'rejected')",
            name="ck_expert_reviews_status",
        ),
        CheckConstraint(
            "status <> 'verified' OR ("
            "verified_diagnosis IS NOT NULL AND length(trim(verified_diagnosis)) > 0 AND "
            "verification_method IS NOT NULL AND length(trim(verification_method)) > 0"
            ")",
            name="ck_expert_reviews_verified_fields",
        ),
        CheckConstraint(
            "status NOT IN ('uncertain', 'rejected') OR "
            "(verification_method IS NOT NULL AND length(trim(verification_method)) > 0)",
            name="ck_expert_reviews_completed_method",
        ),
    )
