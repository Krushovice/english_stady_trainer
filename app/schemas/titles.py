from pydantic import BaseModel

from app.models.learning_profile import CEFRLevel


class TitleResponse(BaseModel):
    title: str
    cefr_grade: CEFRLevel | None
    days_practiced: int
    mistakes_mastered: int
    mistakes_total: int
    review_count: int
