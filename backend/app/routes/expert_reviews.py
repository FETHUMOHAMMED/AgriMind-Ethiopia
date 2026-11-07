from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import exists, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.expert_adjudication import ExpertAdjudication
from app.models.expert_review import ExpertReview
from app.models.field_case import FieldCase
from app.schemas.expert_review import (
    ExpertAdjudicationCreate,
    ExpertAdjudicationResponse,
    ExpertCaseHistoryResponse,
    ExpertReviewCreate,
    ExpertReviewResponse,
    FieldCaseReviewQueueResponse,
)
from app.utils.consent import (
    EXPERT_REVIEW_PURPOSE,
    PRECISE_LOCATION_PURPOSE,
    has_active_data_consent,
)
from app.utils.dependencies import get_db, require_role
from app.utils.taxonomy import APPROVED_TAXONOMY_VERSION, is_approved_diagnosis

router = APIRouter(prefix="/expert-reviews", tags=["expert reviews"])
reviewer = require_role("reviewer")
review_access = require_role("reviewer", "adjudicator")
adjudicator = require_role("adjudicator")


def _review_response(review: ExpertReview, case_id: str) -> dict:
    return {
        "review_id": review.id,
        "field_case_id": case_id,
        "reviewer_user_id": review.reviewer_user_id,
        "status": review.status,
        "verified_diagnosis": review.verified_diagnosis,
        "verification_method": review.verification_method,
        "review_notes": review.review_notes,
        "reviewed_at": review.reviewed_at.isoformat(),
        "created_at": review.created_at.isoformat() if review.created_at else None,
        # A reviewer opinion is never itself a final case decision.
        "is_final": False,
    }


def _adjudication_response(adjudication: ExpertAdjudication, case_id: str) -> dict:
    return {
        "adjudication_id": adjudication.id,
        "field_case_id": case_id,
        "adjudicator_user_id": adjudication.adjudicator_user_id,
        "decision": adjudication.decision,
        "final_diagnosis": adjudication.final_diagnosis,
        "taxonomy_version": adjudication.taxonomy_version,
        "decision_rationale": adjudication.decision_rationale,
        "decided_at": adjudication.decided_at.isoformat(),
        "created_at": (
            adjudication.created_at.isoformat()
            if adjudication.created_at
            else None
        ),
    }


@router.get(
    "/cases/pending",
    response_model=list[FieldCaseReviewQueueResponse],
)
async def get_cases_awaiting_review(
    current_user: dict = Depends(review_access),
    db: Session = Depends(get_db),
):
    adjudication_exists = exists().where(
        ExpertAdjudication.field_case_id == FieldCase.id
    )
    review_count = (
        db.query(func.count(ExpertReview.id))
        .filter(ExpertReview.field_case_id == FieldCase.id)
        .correlate(FieldCase)
        .scalar_subquery()
    )
    cases = (
        db.query(FieldCase, review_count.label("review_count"))
        .filter(~adjudication_exists)
        .order_by(FieldCase.created_at.asc(), FieldCase.id.asc())
        .all()
    )

    return [
        {
            "case_id": case.case_id,
            "prediction_id": case.prediction_id,
            "crop": case.crop,
            "variety": case.variety,
            "plant_part": case.plant_part,
            "growth_stage": case.growth_stage,
            "observed_symptoms": case.observed_symptoms,
            "region": case.region,
            "zone": case.zone,
            "woreda": case.woreda,
            # Precise coordinates are never included in the ordinary review
            # queue. Use the adjudicator-only location endpoint when policy
            # and authorization permit access.
            "latitude": None,
            "longitude": None,
            "collection_date": case.collection_date.isoformat(),
            "consent_status": case.consent_status,
            "created_at": case.created_at.isoformat() if case.created_at else None,
            "review_count": count,
        }
        for case, count in cases
        if has_active_data_consent(db, case.id, EXPERT_REVIEW_PURPOSE)
    ]


@router.get(
    "/cases/{case_id}",
    response_model=ExpertCaseHistoryResponse,
)
async def get_case_review_history(
    case_id: str,
    current_user: dict = Depends(review_access),
    db: Session = Depends(get_db),
):
    del current_user
    case = db.query(FieldCase).filter(FieldCase.case_id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Field case not found")
    if not has_active_data_consent(db, case.id, EXPERT_REVIEW_PURPOSE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Expert review consent is not active for this field case",
        )

    reviews = (
        db.query(ExpertReview)
        .filter(ExpertReview.field_case_id == case.id)
        .order_by(ExpertReview.created_at.asc(), ExpertReview.id.asc())
        .all()
    )
    adjudication = (
        db.query(ExpertAdjudication)
        .filter(ExpertAdjudication.field_case_id == case.id)
        .first()
    )
    return {
        "case_id": case.case_id,
        "reviews": [_review_response(review, case.case_id) for review in reviews],
        "adjudication": (
            _adjudication_response(adjudication, case.case_id)
            if adjudication
            else None
        ),
    }


@router.get("/cases/{case_id}/coordinates")
async def get_case_coordinates(
    case_id: str,
    current_user: dict = Depends(adjudicator),
    db: Session = Depends(get_db),
):
    """Return precise coordinates only to adjudicators with active consent."""
    del current_user
    case = db.query(FieldCase).filter(FieldCase.case_id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Field case not found")
    if not has_active_data_consent(db, case.id, PRECISE_LOCATION_PURPOSE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Precise location consent is not active for this field case",
        )
    return {
        "case_id": case.case_id,
        "latitude": case.latitude,
        "longitude": case.longitude,
    }


@router.post(
    "/",
    response_model=ExpertReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_expert_review(
    review_in: ExpertReviewCreate,
    current_user: dict = Depends(reviewer),
    db: Session = Depends(get_db),
):
    case = db.query(FieldCase).filter(FieldCase.case_id == review_in.field_case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Field case not found")
    if not has_active_data_consent(db, case.id, EXPERT_REVIEW_PURPOSE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Expert review consent is not active for this field case",
        )

    if (
        db.query(ExpertAdjudication)
        .filter(ExpertAdjudication.field_case_id == case.id)
        .first()
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Field case already has a final adjudication",
        )

    review = ExpertReview(
        field_case_id=case.id,
        reviewer_user_id=current_user["user_id"],
        status=review_in.status,
        verified_diagnosis=review_in.verified_diagnosis,
        verification_method=review_in.verification_method,
        review_notes=review_in.review_notes,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This reviewer has already submitted a review for this field case",
        )
    db.refresh(review)

    return _review_response(review, case.case_id)


@router.post(
    "/adjudications/",
    response_model=ExpertAdjudicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_adjudication(
    adjudication_in: ExpertAdjudicationCreate,
    current_user: dict = Depends(adjudicator),
    db: Session = Depends(get_db),
):
    case = (
        db.query(FieldCase)
        .filter(FieldCase.case_id == adjudication_in.field_case_id)
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Field case not found")
    if not has_active_data_consent(db, case.id, EXPERT_REVIEW_PURPOSE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Expert review consent is not active for this field case",
        )

    if (
        db.query(ExpertAdjudication)
        .filter(ExpertAdjudication.field_case_id == case.id)
        .first()
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Field case already has a final adjudication",
        )

    reviews = (
        db.query(ExpertReview)
        .filter(ExpertReview.field_case_id == case.id)
        .order_by(ExpertReview.created_at.asc(), ExpertReview.id.asc())
        .all()
    )
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="At least one independent expert review is required",
        )

    verified_diagnoses = {
        review.verified_diagnosis.strip().casefold()
        for review in reviews
        if review.status == "verified"
        and review.verified_diagnosis
        and review.verified_diagnosis.strip()
    }
    if adjudication_in.decision in {"agreement", "disagreement"}:
        if adjudication_in.taxonomy_version != APPROVED_TAXONOMY_VERSION:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="An approved diagnosis taxonomy version is required",
            )
        if not is_approved_diagnosis(
            adjudication_in.final_diagnosis,
            adjudication_in.taxonomy_version,
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Final diagnosis is not in the approved taxonomy",
            )
        if len(reviews) < 2 or len(verified_diagnoses) == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agreement or disagreement requires at least two diagnosed expert reviews",
            )
        if adjudication_in.decision == "agreement" and len(verified_diagnoses) != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agreement requires matching expert diagnoses",
            )
        if adjudication_in.decision == "agreement":
            agreed_diagnosis = next(iter(verified_diagnoses))
            if adjudication_in.final_diagnosis.strip().casefold() != agreed_diagnosis:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Agreement final diagnosis must match the expert diagnoses",
                )
        if adjudication_in.decision == "disagreement" and len(verified_diagnoses) < 2:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Disagreement requires differing expert diagnoses",
            )

    adjudication = ExpertAdjudication(
        field_case_id=case.id,
        adjudicator_user_id=current_user["user_id"],
        decision=adjudication_in.decision,
        final_diagnosis=adjudication_in.final_diagnosis,
        taxonomy_version=adjudication_in.taxonomy_version,
        decision_rationale=adjudication_in.decision_rationale,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(adjudication)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Field case already has a final adjudication",
        )
    db.refresh(adjudication)

    return _adjudication_response(adjudication, case.case_id)
