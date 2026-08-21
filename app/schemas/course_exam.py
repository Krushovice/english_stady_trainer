import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.exercise import ExercisePublicResponse


class CourseExamStatusResponse(BaseModel):
    exam_available: bool
    passed: bool
    attempts_used_in_window: int
    attempts_per_window: int
    cooldown_until: datetime | None
    in_progress_attempt_id: uuid.UUID | None
    in_progress_expires_at: datetime | None
    certificate_available: bool
    earned_at: datetime | None


class CourseExamAttemptResponse(BaseModel):
    attempt_id: uuid.UUID
    expires_at: datetime
    exercises: list[ExercisePublicResponse]


class CourseExamAnswer(BaseModel):
    exercise_id: uuid.UUID
    submitted_answer: dict


class CourseExamSubmitRequest(BaseModel):
    answers: list[CourseExamAnswer]


class CourseExamResultResponse(BaseModel):
    attempt_id: uuid.UUID
    score: float
    passed: bool
    correct_count: int
    total_count: int
