from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String, nullable=True)
    # SHA-256 of the original uploaded bytes. Nullable for legacy predictions
    # whose original upload cannot be reconstructed safely.
    image_sha256 = Column(String(64), nullable=True, index=True)
    image_processing_history = Column(String(2000), nullable=True)
    disease = Column(String, nullable=False)
    confidence = Column(Float)
    recommendation = Column(String)
    # These remain nullable because historical rows did not record them and
    # the current checkpoint may not provide a verifiable version identifier.
    model_version = Column(String(100), nullable=True)
    inference_timestamp = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
