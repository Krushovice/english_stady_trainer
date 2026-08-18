import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.ai import WritingFeedbackResponse


class SpeakingAttemptResponse(BaseModel):
    id: uuid.UUID
    lesson_title: str
    prompt: str
    transcript: str | None
    feedback: WritingFeedbackResponse | None
    generated_at: datetime
    submitted_at: datetime | None
