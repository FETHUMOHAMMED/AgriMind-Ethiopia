from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.utils.dependencies import get_db, require_role
from app.utils.training_eligibility import build_training_eligibility_report


router = APIRouter(prefix="/training-eligibility", tags=["training eligibility"])
adjudicator = require_role("adjudicator")


@router.get("/report")
async def get_training_eligibility_report(
    current_user: dict = Depends(adjudicator),
    db: Session = Depends(get_db),
):
    """Return an aggregate-only eligibility report to trusted adjudicators."""
    del current_user
    return build_training_eligibility_report(db)
