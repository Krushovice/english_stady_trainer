import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.learning_profile import CEFRLevel, cefr_level_type


class LevelExamAttempt(Base):
    """One attempt at a level's exit exam.

    `exercise_ids` freezes the question set selected for this attempt (order
    preserved) so scoring is reproducible even though selection is random per
    attempt. `answers` is empty until submitted. Exam answers are graded
    through the same per-type scorers as lesson exercises, but deliberately
    don't create `ExerciseAttempt` rows or feed spaced repetition / mistake
    tracking — same precedent as placement-test answers (see decisions.md).
    """

    __tablename__ = "level_exam_attempts"
    __table_args__ = (Index("ix_level_exam_attempts_user_level", "user_id", "level"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[CEFRLevel] = mapped_column(cefr_level_type, nullable=False)
    exercise_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    passed: Mapped[bool | None] = mapped_column(nullable=True)
