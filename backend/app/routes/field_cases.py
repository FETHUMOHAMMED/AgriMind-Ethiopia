import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.consent import ConsentRecord
from app.models.field_case import FieldCase
from app.models.prediction import Prediction
from app.schemas.field_case import (
    ConsentChangeCreate,
    ConsentRecordResponse,
    FieldCaseCreate,
    FieldCaseCreated,
)
from app.utils.dependencies import get_current_user, get_db

router = APIRouter(prefix="/field-cases", tags=["field cases"])


def _consent_response(record: ConsentRecord, case_id: str) -> dict:
    return {
        "consent_id": record.id,
        "field_case_id": case_id,
        "purpose": record.purpose,
        "status": record.status,
        "policy_version": record.policy_version,
        "recorded_at": record.recorded_at.isoformat(),
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def _declarations(case_in: FieldCaseCreate) -> list[tuple[str, str, str | None]]:
    declarations = case_in.consents
    result: list[tuple[str, str, str | None]] = [
        ("observation_collection", case_in.consent_status, None)
    ]
    if declarations is None:
        return result

    for purpose, declaration in (
        ("observation_collection", declarations.observation_collection),
        ("expert_review", declarations.expert_review),
        ("ai_training", declarations.ai_training),
        ("precise_location", declarations.precise_location),
    ):
        if declaration is not None:
            result = [item for item in result if item[0] != purpose]
            result.append((purpose, declaration.status, declaration.policy_version))
    return result


@router.post("/", response_model=FieldCaseCreated, status_code=status.HTTP_201_CREATED)
async def create_field_case(
    case_in: FieldCaseCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if case_in.consent_status != "granted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Observation collection consent is required",
        )

    if case_in.prediction_id is not None:
        prediction = (
            db.query(Prediction)
            .filter(
                Prediction.id == case_in.prediction_id,
                Prediction.user_id == current_user["user_id"],
            )
            .first()
        )
        if prediction is None:
            raise HTTPException(status_code=404, detail="Prediction not found")

    case = FieldCase(
        case_id=f"FC-{uuid.uuid4()}",
        collector_user_id=current_user["user_id"],
        prediction_id=case_in.prediction_id,
        crop=case_in.crop,
        variety=case_in.variety,
        plant_part=case_in.plant_part,
        growth_stage=case_in.growth_stage,
        observed_symptoms=case_in.observed_symptoms,
        region=case_in.region,
        zone=case_in.zone,
        woreda=case_in.woreda,
        latitude=case_in.latitude,
        longitude=case_in.longitude,
        collection_date=case_in.collection_date,
        consent_status=case_in.consent_status,
    )
    db.add(case)
    try:
        db.flush()
        recorded_at = datetime.now(timezone.utc)
        for purpose, consent_status, policy_version in _declarations(case_in):
            db.add(
                ConsentRecord(
                    field_case_id=case.id,
                    subject_user_id=current_user["user_id"],
                    purpose=purpose,
                    status=consent_status,
                    policy_version=policy_version,
                    recorded_at=recorded_at,
                )
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field case could not be recorded",
        )
    db.refresh(case)

    # Coordinates and collector identity are intentionally omitted from this
    # acknowledgement. They are available only in reviewer-authorized detail.
    return {
        "case_id": case.case_id,
        "prediction_id": case.prediction_id,
        "crop": case.crop,
        "collection_date": case.collection_date.isoformat(),
        "consent_status": case.consent_status,
        "created_at": case.created_at.isoformat() if case.created_at else None,
    }


@router.get(
    "/{case_id}/consents",
    response_model=list[ConsentRecordResponse],
)
async def get_case_consents(
    case_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = (
        db.query(FieldCase)
        .filter(
            FieldCase.case_id == case_id,
            FieldCase.collector_user_id == current_user["user_id"],
        )
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Field case not found")

    records = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.field_case_id == case.id)
        .order_by(ConsentRecord.recorded_at.asc(), ConsentRecord.id.asc())
        .all()
    )
    return [_consent_response(record, case.case_id) for record in records]


@router.post(
    "/{case_id}/consents",
    response_model=ConsentRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_consent_change(
    case_id: str,
    consent_in: ConsentChangeCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = (
        db.query(FieldCase)
        .filter(
            FieldCase.case_id == case_id,
            FieldCase.collector_user_id == current_user["user_id"],
        )
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Field case not found")

    record = ConsentRecord(
        field_case_id=case.id,
        subject_user_id=current_user["user_id"],
        purpose=consent_in.purpose,
        status=consent_in.status,
        policy_version=consent_in.policy_version,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent change could not be recorded",
        )
    db.refresh(record)
    return _consent_response(record, case.case_id)
