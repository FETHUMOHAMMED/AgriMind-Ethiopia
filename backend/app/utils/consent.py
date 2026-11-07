from sqlalchemy import and_, exists, or_
from sqlalchemy.orm import Session, aliased

from app.models.consent import ConsentRecord
from app.models.field_case import FieldCase


OBSERVATION_PURPOSE = "observation_collection"
EXPERT_REVIEW_PURPOSE = "expert_review"
TRAINING_PURPOSE = "ai_training"
PRECISE_LOCATION_PURPOSE = "precise_location"


def latest_consent(
    db: Session,
    field_case_id: int,
    purpose: str,
) -> ConsentRecord | None:
    return (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.field_case_id == field_case_id,
            ConsentRecord.purpose == purpose,
        )
        .order_by(ConsentRecord.recorded_at.desc(), ConsentRecord.id.desc())
        .first()
    )


def has_active_consent(db: Session, field_case_id: int, purpose: str) -> bool:
    record = latest_consent(db, field_case_id, purpose)
    return record is not None and record.status == "granted"


def has_active_data_consent(db: Session, field_case_id: int, purpose: str) -> bool:
    """Require collection consent plus the purpose-specific consent.

    A withdrawal of collection consent therefore blocks all future use even if
    a purpose-specific grant remains in the historical event stream.
    """
    return has_active_consent(db, field_case_id, OBSERVATION_PURPOSE) and has_active_consent(
        db, field_case_id, purpose
    )


def training_consent_eligible_cases(db: Session):
    """Return cases with current collection and training consent only.

    This is a lower-level consent query. It is intentionally not the ML
    eligibility policy; callers requiring training eligibility must use
    ``app.utils.training_eligibility``.

    Cases without purpose-specific records, or with a latest denied or
    withdrawn event, are excluded.
    """
    training_record = aliased(ConsentRecord)
    newer_training_record = aliased(ConsentRecord)
    observation_record = aliased(ConsentRecord)
    newer_observation_record = aliased(ConsentRecord)

    def is_newer(candidate, current):
        return or_(
            candidate.recorded_at > current.recorded_at,
            and_(
                candidate.recorded_at == current.recorded_at,
                candidate.id > current.id,
            ),
        )

    return (
        db.query(FieldCase)
        .join(training_record, training_record.field_case_id == FieldCase.id)
        .join(observation_record, observation_record.field_case_id == FieldCase.id)
        .filter(
            training_record.purpose == TRAINING_PURPOSE,
            training_record.status == "granted",
            ~exists().where(
                and_(
                    newer_training_record.field_case_id == FieldCase.id,
                    newer_training_record.purpose == TRAINING_PURPOSE,
                    is_newer(newer_training_record, training_record),
                )
            ),
            observation_record.purpose == OBSERVATION_PURPOSE,
            observation_record.status == "granted",
            ~exists().where(
                and_(
                    newer_observation_record.field_case_id == FieldCase.id,
                    newer_observation_record.purpose == OBSERVATION_PURPOSE,
                    is_newer(newer_observation_record, observation_record),
                )
            ),
        )
    )
