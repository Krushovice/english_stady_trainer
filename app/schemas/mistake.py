import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field

from app.models.user_mistake import MistakeStatus
from app.schemas.course import GrammarTopicResponse


class UserMistakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    grammar_topic: GrammarTopicResponse
    status: MistakeStatus
    total_attempts: int
    incorrect_attempts: int
    last_attempt_at: datetime

    @computed_field
    @property
    def error_rate(self) -> Decimal:
        if self.total_attempts == 0:
            return Decimal(0)
        return Decimal(self.incorrect_attempts) / Decimal(self.total_attempts)
