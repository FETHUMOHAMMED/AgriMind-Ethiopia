import mimetypes
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.field_case import FieldCase
from app.models.prediction import Prediction
from app.utils.consent import EXPERT_REVIEW_PURPOSE, has_active_data_consent
from app.utils.dependencies import get_current_user
from app.routes.predict import UPLOAD_DIR

router = APIRouter(tags=["uploads"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/uploads/predictions/{filename}")
async def get_prediction_image(
    filename: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Serve prediction images only to their owner or an authorized reviewer.

    The filename is treated as an opaque stored identifier. Path traversal is
    rejected, and database ownership/consent checks happen before the file is
    served.
    """
    if Path(filename).name != filename or filename in {"", ".", ".."}:
        raise HTTPException(status_code=404, detail="Image not found")

    stored_path = os.path.join(UPLOAD_DIR, filename)
    prediction = (
        db.query(Prediction)
        .filter(Prediction.image_url == stored_path)
        .first()
    )
    if prediction is None:
        raise HTTPException(status_code=404, detail="Image not found")

    owner = prediction.user_id == current_user["user_id"]
    reviewer = current_user.get("role") in {"reviewer", "adjudicator"}
    review_authorized = False
    if reviewer:
        review_authorized = (
            db.query(FieldCase)
            .filter(FieldCase.prediction_id == prediction.id)
            .all()
        )
        review_authorized = any(
            has_active_data_consent(db, case.id, EXPERT_REVIEW_PURPOSE)
            for case in review_authorized
        )

    if not owner and not review_authorized:
        raise HTTPException(status_code=404, detail="Image not found")

    base_dir = Path(UPLOAD_DIR).resolve()
    image_path = (base_dir / filename).resolve()
    if base_dir not in image_path.parents or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    media_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    return FileResponse(str(image_path), media_type=media_type, filename=image_path.name)
