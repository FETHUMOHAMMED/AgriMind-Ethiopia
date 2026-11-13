from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ReviewStatus = Literal["pending", "verified", "uncertain", "rejected"]
AdjudicationDecision = Literal[
    "agreement",
    "disagreement",
    "uncertain",
    "rejected",
]


class ExpertReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_case_id: str = Field(min_length=1, max_length=40)
    status: ReviewStatus
    verified_diagnosis: str | None = Field(default=None, max_length=200)
    verification_method: str | None = Field(default=None, max_length=200)
    review_notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_verification_fields(self):
        if self.status == "verified":
            if not self.verified_diagnosis or not self.verified_diagnosis.strip():
                raise ValueError(
                    "verified_diagnosis is required for a verified review"
                )
            if not self.verification_method or not self.verification_method.strip():
                raise ValueError(
                    "verification_method is required for a verified review"
                )
        elif self.status in {"uncertain", "rejected"}:
            if not self.verification_method or not self.verification_method.strip():
                raise ValueError(
                    "verification_method is required for a completed review"
                )
        return self
    


class ExpertReviewResponse(BaseModel):
    review_id: int
    field_case_id: str
    reviewer_user_id: int
    status: ReviewStatus
    verified_diagnosis: str | None
    verification_method: str | None
    review_notes: str | None
    reviewed_at: str
    created_at: str | None
    is_final: bool = False


class ExpertAdjudicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_case_id: str = Field(min_length=1, max_length=40)
    decision: AdjudicationDecision
    final_diagnosis: str | None = Field(default=None, max_length=200)
    taxonomy_version: str | None = Field(default=None, max_length=100)
    decision_rationale: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="after")
    def validate_final_diagnosis(self):
        if self.decision in {"agreement", "disagreement"}:
            if not self.final_diagnosis or not self.final_diagnosis.strip():
                raise ValueError(
                    "final_diagnosis is required for an agreement or disagreement decision"
                )
        elif self.final_diagnosis is not None or self.taxonomy_version is not None:
            raise ValueError(
                "uncertain and rejected decisions cannot contain a final diagnosis or taxonomy"
            )
        return self
    
    
    @field_validator("decision_rationale")
    @classmethod
    def _validate_decision_rationale_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision_rationale must not be whitespace-only")
        return v


class ExpertAdjudicationResponse(BaseModel):
    adjudication_id: int
    field_case_id: str
    adjudicator_user_id: int
    decision: AdjudicationDecision
    final_diagnosis: str | None
    taxonomy_version: str | None
    decision_rationale: str
    decided_at: str
    created_at: str | None


class FieldCaseReviewQueueResponse(BaseModel):
    case_id: str
    prediction_id: int | None
    crop: str
    variety: str | None
    plant_part: str
    growth_stage: str
    observed_symptoms: str
    region: str | None
    zone: str | None
    woreda: str | None
    latitude: float | None
    longitude: float | None
    collection_date: date
    consent_status: str
    created_at: str | None
    review_count: int


class ExpertCaseHistoryResponse(BaseModel):
    case_id: str
    reviews: list[ExpertReviewResponse]
    adjudication: ExpertAdjudicationResponse | None
