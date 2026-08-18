import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SpeakingAttempt(Base):
    """One Speaking practice round: an AI-generated prompt, the learner's
    transcribed spoken answer, and AI feedback on it.

    `transcript`/`feedback`/`submitted_at` are nullable — a row is created
    when the prompt is generated and filled in once audio is submitted, the
    same two-step generate-then-submit shape as `Homework`/`HomeworkAttempt`.
    Retry (CLAUDE.md's "Speaking" flow) means generating a new prompt/attempt,
    not resubmitting audio to an already-submitted one.
    """

    __tablename__ = "speaking_attempts"
    __table_args__ = (Index("ix_speaking_attempts_user_generated_at", "user_id", "generated_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="RESTRICT"), nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lesson: Mapped["Lesson"] = relationship()  # noqa: F821
