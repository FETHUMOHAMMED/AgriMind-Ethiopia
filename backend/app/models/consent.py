from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.database import Base


class ConsentRecord(Base):
    """Append-only consent event for a field case and a specific purpose.

    The latest event for a purpose is the current consent state. Historical
    events are retained so withdrawal and re-grant decisions remain auditable.
    ``field_case_id`` is nullable so a future pre-collection consent flow can
    record a decision before a case exists; the current field-case route writes
    records after the case is created in the same transaction.
    """

    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    field_case_id = Column(
        Integer,
        ForeignKey("field_cases.id"),
        nullable=True,
        index=True,
    )
    subject_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String(40), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    policy_version = Column(String(100), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "purpose IN ('observation_collection', 'expert_review', "
            "'ai_training', 'precise_location')",
            name="ck_consent_records_purpose",
        ),
        CheckConstraint(
            "status IN ('granted', 'denied', 'withdrawn')",
            name="ck_consent_records_status",
        ),
        CheckConstraint(
            "policy_version IS NULL OR length(trim(policy_version)) > 0",
            name="ck_consent_records_policy_version",
        ),
    )
