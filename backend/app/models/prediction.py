from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String, nullable=True)
    disease = Column(String, nullable=False)
    confidence = Column(Float)
    recommendation = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())