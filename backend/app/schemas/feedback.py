from pydantic import BaseModel

class FeedbackCreate(BaseModel):
    prediction_id: int
    correct: bool
    comment: str | None = None