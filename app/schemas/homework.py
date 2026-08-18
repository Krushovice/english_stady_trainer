import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.ai import WritingFeedbackResponse


class HomeworkTaskResponse(BaseModel):
    id: str
    instruction: str


class HomeworkAttemptResponse(BaseModel):
    id: uuid.UUID
    task_id: str
    submitted_text: str
    feedback: WritingFeedbackResponse
    submitted_at: datetime


class HomeworkResponse(BaseModel):
    id: uuid.UUID
    lesson_title: str
    tasks: list[HomeworkTaskResponse]
    attempts: list[HomeworkAttemptResponse]
    generated_at: datetime


class SubmitHomeworkTaskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
