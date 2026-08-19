import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.learning_profile import CEFRLevel
from app.schemas.exercise import ExercisePublicResponse


class ExamStatusResponse(BaseModel):
    level: CEFRLevel
    exam_available: bool
    passed: bool
    attempts_used_in_window: int
    attempts_per_window: int
    cooldown_until: datetime | None
    in_progress_attempt_id: uuid.UUID | None
    in_progress_expires_at: datetime | None


class ExamAttemptResponse(BaseModel):
    attempt_id: uuid.UUID
    expires_at: datetime
    exercises: list[ExercisePublicResponse]


class ExamAnswer(BaseModel):
    exercise_id: uuid.UUID
    submitted_answer: dict


class ExamSubmitRequest(BaseModel):
    answers: list[ExamAnswer]


class ExamResultResponse(BaseModel):
    attempt_id: uuid.UUID
    score: float
    passed: bool
    correct_count: int
    total_count: int
