from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.database import Base


class ExpertAdjudication(Base):
    """Immutable final decision for a field case.

    Individual expert opinions remain in ``expert_reviews``. This table is a
    separate, one-per-case final decision and never overwrites those opinions.
    """

    __tablename__ = "expert_adjudications"

    id = Column(Integer, primary_key=True, index=True)
    field_case_id = Column(
        Integer,
        ForeignKey("field_cases.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    adjudicator_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    decision = Column(String(32), nullable=False, index=True)
    final_diagnosis = Column(String(200), nullable=True)
    taxonomy_version = Column(String(100), nullable=True)
    decision_rationale = Column(String(4000), nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
    CheckConstraint(
        "decision IN ('agreement', 'disagreement', 'uncertain', 'rejected')",
        name="ck_expert_adjudications_decision",
    ),
    CheckConstraint(
        "decision NOT IN ('agreement', 'disagreement') OR "
        "(final_diagnosis IS NOT NULL AND length(trim(final_diagnosis)) > 0)",
        name="ck_expert_adjudications_final_diagnosis",
    ),
    CheckConstraint(
        "length(trim(decision_rationale)) > 0",
        name="ck_expert_adjudications_decision_rationale_not_blank",
    ),
)
