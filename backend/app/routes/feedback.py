from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.feedback import Feedback
from app.models.prediction import Prediction
from app.schemas.feedback import FeedbackCreate
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# 1. Submit Feedback
# -------------------------------------------------------------------
@router.post("/")
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # FIX 9: Verify the prediction exists and belongs to the current user
    prediction = (
        db.query(Prediction)
        .filter(
            Prediction.id == feedback.prediction_id,
            Prediction.user_id == current_user["user_id"],
        )
        .first()
    )
    if prediction is None:
        raise HTTPException(
            status_code=404,
            detail="Prediction not found.",
        )

    # Now safe to create the feedback record
    entry = Feedback(
        user_id=current_user["user_id"],
        prediction_id=feedback.prediction_id,
        correct=feedback.correct,
        comment=feedback.comment,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "message": "Feedback submitted",
        "feedback_id": entry.id,
    }


# -------------------------------------------------------------------
# 2. Get Feedback History (for current user)
# -------------------------------------------------------------------
@router.get("/")
async def get_feedback_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedbacks = (
        db.query(Feedback)
        .filter(Feedback.user_id == current_user["user_id"])
        .order_by(Feedback.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "id": f.id,
            "prediction_id": f.prediction_id,
            "correct": f.correct,
            "comment": f.comment,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in feedbacks
    ]