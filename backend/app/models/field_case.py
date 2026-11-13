from sqlalchemy import CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database.database import Base


class FieldCase(Base):
    __tablename__ = "field_cases"

    id = Column(Integer, primary_key=True, index=True)
    # ``FC-`` plus a canonical UUID is 39 characters.
    case_id = Column(String(40), unique=True, index=True, nullable=False)
    collector_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True, index=True)
    crop = Column(String(100), nullable=False)
    variety = Column(String(100), nullable=True)
    plant_part = Column(String(100), nullable=False)
    growth_stage = Column(String(100), nullable=False)
    observed_symptoms = Column(String(4000), nullable=False)
    region = Column(String(100), nullable=True)
    zone = Column(String(100), nullable=True)
    woreda = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    collection_date = Column(Date, nullable=False)
    consent_status = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
    CheckConstraint(
        "consent_status IN ('granted', 'denied')",
        name="ck_field_cases_consent_status",
    ),
    CheckConstraint(
        "latitude IS NULL OR latitude BETWEEN -90 AND 90",
        name="ck_field_cases_latitude",
    ),
    CheckConstraint(
        "longitude IS NULL OR longitude BETWEEN -180 AND 180",
        name="ck_field_cases_longitude",
    ),
    CheckConstraint(
        "length(trim(observed_symptoms)) > 0",
        name="ck_field_cases_observed_symptoms_not_blank",
    ),
)
    
    
