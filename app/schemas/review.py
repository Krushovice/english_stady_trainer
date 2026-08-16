import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.review_item import ReviewItemType
from app.schemas.course import GrammarTopicResponse, VocabularyResponse
from app.schemas.exercise import ExercisePublicResponse


class ReviewItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_type: ReviewItemType
    due_at: datetime
    interval_days: int
    review_count: int
    vocabulary: VocabularyResponse | None = None
    grammar_topic: GrammarTopicResponse | None = None
    exercise: ExercisePublicResponse | None = None


class CompleteReviewRequest(BaseModel):
    is_correct: bool
