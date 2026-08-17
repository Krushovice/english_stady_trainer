from pydantic import BaseModel, Field


class WritingFeedbackRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class WritingFeedbackResponse(BaseModel):
    good: str
    grammar: str
    vocabulary: str
    natural_version: str
    try_again: str
