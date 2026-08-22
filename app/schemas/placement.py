import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.exercise import Skill
from app.models.learning_profile import CEFRLevel


class PlacementAnswer(BaseModel):
    exercise_id: uuid.UUID
    submitted_answer: dict


class PlacementSubmitRequest(BaseModel):
    answers: list[PlacementAnswer]


class SkillLevelResult(BaseModel):
    skill: Skill
    level: CEFRLevel | None
    correct: int | None = None
    total: int | None = None


class RecommendedModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    level_code: CEFRLevel


class PlacementResultResponse(BaseModel):
    overall_level: CEFRLevel | None
    skills: list[SkillLevelResult]
    recommended_modules: list[RecommendedModuleResponse]
    placement_completed_at: datetime | None


class ChooseStartingPointRequest(BaseModel):
    choice: Literal["review", "assessed"]
