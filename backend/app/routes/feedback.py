from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = Feedback(
        user_id=current_user["user_id"],
        prediction_id=feedback.prediction_id,
        correct=feedback.correct,
        comment=feedback.comment
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"message": "Feedback submitted", "feedback_id": entry.id}

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
            "created_at": f.created_at.isoformat()
        }
        for f in feedbacks
    ]