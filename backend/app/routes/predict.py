import hashlib
import io
import json
import os
import uuid
from datetime import datetime, timezone
from PIL import Image
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import SessionLocal
from app.models.prediction import Prediction
from app.ai import real_predictor
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

    # FIX 5: Run inference BEFORE saving anything
    # FIX 6: Map errors to correct HTTP status codes
    # FIX 7: Service Unavailable is now handled via RuntimeError in predictor
    try:
        result = predict_disease(contents)
        print(f"PREDICTION RESULT: {result}")
    except ValueError:
        # FIX 4: Invalid image bytes → 400
        raise HTTPException(
            status_code=400,
            detail="Invalid image data.",
        )
    except RuntimeError:
        # FIX 7: Model unavailable or inference failed → 503
        raise HTTPException(
            status_code=503,
            detail="The prediction service is unavailable. Please try again later.",
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Please try again.",
        )

    # FIX 5: Only NOW save the image and database record
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    inference_timestamp = datetime.now(timezone.utc)
    image_sha256 = hashlib.sha256(contents).hexdigest()
    image_processing_history = json.dumps(
        {
            "schema_version": 1,
            "operations": [],
            "original_bytes_preserved": True,
        },
        separators=(",", ":"),
    )

    try:
        with open(file_path, "wb") as f:
            f.write(contents)

        prediction = Prediction(
            user_id=current_user["user_id"],
            image_url=file_path,
            image_sha256=image_sha256,
            image_processing_history=image_processing_history,
            disease=result["name"],
            confidence=result["confidence"],
            recommendation=result["recommendation"],
            model_version=getattr(real_predictor, "MODEL_VERSION", None),
            inference_timestamp=inference_timestamp,
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
    except Exception:
        db.rollback()
        # FIX 8: Avoid leaving an orphaned upload if DB save fails
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=500,
            detail="Failed to save prediction.",
        )

    return {
        "prediction_id": prediction.id,
        "disease": result["name"],
        "confidence": result["confidence"],
        "recommendation": result["recommendation"],
        "symptoms": result.get("symptoms", ""),
        "prevention": result.get("prevention", ""),
        "expert_help": result.get("expert_help", ""),
        "diagnosed_by": current_user["email"],
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
            # Preserve the response field while avoiding filesystem paths.
            "image_path": (
                f"/uploads/predictions/{os.path.basename(p.image_url)}"
                if p.image_url
                else None
            ),
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

    # Ethiopian day (EAT = UTC+3, no DST). Compute the UTC range covering
    # Ethiopian "today" (start-of-day to start-of-next-day in EAT), then
    # compare against the stored UTC timestamps. Works on SQLite and PostgreSQL;
    # uses index-friendly range comparison (no func.date, no dialect functions).
    from datetime import datetime, timezone, timedelta
    EAT = timezone(timedelta(hours=3))
    now_eat = datetime.now(EAT)
    start_eat = now_eat.replace(hour=0, minute=0, second=0, microsecond=0)
    end_eat = start_eat + timedelta(days=1)
    start_utc = start_eat.astimezone(timezone.utc)
    end_utc = end_eat.astimezone(timezone.utc)

    today = db.query(Prediction).filter(
        Prediction.user_id == current_user["user_id"],
        Prediction.created_at >= start_utc,
        Prediction.created_at < end_utc,
    ).count()
    
    return {
        "total_predictions": total,
        "today_predictions": today
    }
