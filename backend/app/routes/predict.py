import os
import uuid
import io
from PIL import Image
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import SessionLocal
from app.models.prediction import Prediction
from app.utils.dependencies import get_current_user
from app.ai.real_predictor import predict_disease

router = APIRouter(prefix="/predict", tags=["prediction"])

UPLOAD_DIR = "uploads/predictions"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "jfif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# 1. Upload and predict
# -------------------------------------------------------------------
@router.post("/")
async def predict(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Read file contents
    contents = await file.read()
    
    # Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Validate file extension
    ext = os.path.splitext(file.filename or ".jpg")[1].lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not allowed")
    
    # Save image
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Get prediction (with error handling)
    try:
        result = predict_disease(contents)
        print(f"PREDICTION RESULT: {result}")
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed. Please try again.")
    
    # Save to DB
    try:
        prediction = Prediction(
            user_id=current_user["user_id"],
            image_url=file_path,
            disease=result["name"],
            confidence=result["confidence"],
            recommendation=result["recommendation"]
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save prediction")
    
    return {
        "prediction_id": prediction.id,
        "disease": result["name"],
        "confidence": result["confidence"],
        "recommendation": result["recommendation"],
        "symptoms": result.get("symptoms", ""),
        "prevention": result.get("prevention", ""),
        "expert_help": result.get("expert_help", ""),
        "diagnosed_by": current_user["email"]
    }


# -------------------------------------------------------------------
# 2. Prediction History
# -------------------------------------------------------------------
@router.get("/history")
async def get_prediction_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    predictions = (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user["user_id"])
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": p.id,
            "disease": p.disease,
            "confidence": p.confidence,
            "recommendation": p.recommendation,
            "image_path": p.image_url,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in predictions
    ]


# -------------------------------------------------------------------
# 3. Dashboard Stats
# -------------------------------------------------------------------
@router.get("/stats")
async def get_prediction_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total = db.query(Prediction).filter(Prediction.user_id == current_user["user_id"]).count()
    today = db.query(Prediction).filter(
        Prediction.user_id == current_user["user_id"],
        func.date(Prediction.created_at) == func.date("now")
    ).count()
    
    return {
        "total_predictions": total,
        "today_predictions": today
    }