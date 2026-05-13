import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.prediction import Prediction
from app.utils.dependencies import get_current_user
from app.ai.predictor import predict_disease
from app.ai.real_predictor import predict_disease 

router = APIRouter(prefix="/predict", tags=["prediction"])

UPLOAD_DIR = "uploads/predictions"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def predict(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --- 1. Save the uploaded file ---
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file.file.seek(0)
    image_bytes = file.file.read()
    
    # --- 2. Get AI prediction (fake for now) ---
    result = predict_disease()

    # --- 3. Save to database ---
    prediction_entry = Prediction(
        user_id=current_user["user_id"],
        image_url=file_path,          # store relative path
        disease=result["name"],
        confidence=result["confidence"],
        recommendation=result["recommendation"]
    )
    db.add(prediction_entry)
    db.commit()
    db.refresh(prediction_entry)

    return {
        "prediction_id": prediction_entry.id,
        "disease": result["name"],
        "confidence": result["confidence"],
        "recommendation": result["recommendation"],
        "image_saved": file_path,
        "diagnosed_by": current_user["email"]
    }
    
@router.get("/history")
async def get_prediction_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    predictions = (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user["user_id"])
        .order_by(Prediction.created_at.desc())
        .limit(50)   # limit to last 50
        .all()
    )
    return [
        {
            "id": p.id,
            "disease": p.disease,
            "confidence": p.confidence,
            "recommendation": p.recommendation,
            "image_path": p.image_url,
            "created_at": p.created_at.isoformat()
        }
        for p in predictions
    ]    