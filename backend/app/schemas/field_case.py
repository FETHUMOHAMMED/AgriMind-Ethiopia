from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ConsentPurpose = Literal[
    "observation_collection",
    "expert_review",
    "ai_training",
    "precise_location",
]
ConsentEventStatus = Literal["granted", "denied", "withdrawn"]


class ConsentDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["granted", "denied"]
    policy_version: str = Field(min_length=1, max_length=100)


class FieldCaseConsentDeclarations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_collection: ConsentDeclaration | None = None
    expert_review: ConsentDeclaration | None = None
    ai_training: ConsentDeclaration | None = None
    precise_location: ConsentDeclaration | None = None


class FieldCaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # A supplied prediction is optional. The collector identity is never a
    # request field; it is derived from the authenticated database user.
    prediction_id: int | None = Field(default=None, gt=0)
    crop: str = Field(min_length=1, max_length=100)
    variety: str | None = Field(default=None, max_length=100)
    plant_part: str = Field(min_length=1, max_length=100)
    growth_stage: str = Field(min_length=1, max_length=100)
    observed_symptoms: str = Field(min_length=1, max_length=4000)
    region: str | None = Field(default=None, max_length=100)
    zone: str | None = Field(default=None, max_length=100)
    woreda: str | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    collection_date: date
    consent_status: Literal["granted", "denied"]
    # ``consent_status`` remains as the legacy observation-consent field for
    # existing clients. New clients should send purpose-specific declarations.
    consents: FieldCaseConsentDeclarations | None = None

    @model_validator(mode="after")
    def validate_consent_relationships(self):
        declarations = self.consents
        observation = declarations.observation_collection if declarations else None
        precise_location = declarations.precise_location if declarations else None

        if observation is not None and observation.status != self.consent_status:
            raise ValueError(
                "observation_collection consent must match consent_status"
            )

        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")

        if self.latitude is not None and (
            precise_location is None or precise_location.status != "granted"
        ):
            raise ValueError(
                "precise_location consent is required before coordinates are collected"
            )
        return self
         
    @field_validator("observed_symptoms")
    @classmethod
    def _validate_observed_symptoms_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("observed_symptoms must not be whitespace-only")
        return v
    
    
           
class ConsentChangeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: ConsentPurpose
    status: ConsentEventStatus
    policy_version: str = Field(min_length=1, max_length=100)


class ConsentRecordResponse(BaseModel):
    consent_id: int
    field_case_id: str
    purpose: ConsentPurpose
    status: ConsentEventStatus
    policy_version: str | None
    recorded_at: str
    created_at: str | None


class FieldCaseCreated(BaseModel):
    case_id: str
    prediction_id: int | None
    crop: str
    collection_date: date
    consent_status: str
    created_at: str | None
