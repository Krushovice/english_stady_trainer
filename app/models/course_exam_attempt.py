import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CourseExamAttempt(Base):
    """One attempt at the course-wide final exam (the 5th exam, gating the
    completion certificate — see docs/decisions.md).

    Same shape as `LevelExamAttempt` but spans all four CEFR levels, so
    there's no `level` column. `exercise_ids` freezes both the question set
    *and* its order for this attempt — here the order carries real meaning
    (easy → hard, picked by `CourseExamService._pick_easy_to_hard`), so
    preserving it matters even more than in the per-level exam. Graded
    answers write `ExerciseAttempt` rows tagged `source=FINAL_EXAM`, kept
    out of mistake/spaced-repetition tracking, same as the level exam and
    the placement test.
    """

    __tablename__ = "course_exam_attempts"
    __table_args__ = (Index("ix_course_exam_attempts_user", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    exercise_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    passed: Mapped[bool | None] = mapped_column(nullable=True)
