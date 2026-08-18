import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Homework(Base):
    """A short, AI-generated set of writing tasks reinforcing one lesson.

    `tasks` is a JSON list, not a separate table — generated, read-together
    content, same trust-the-shape pattern as `Exercise.answer_key` and
    `LessonBlock.content`. Each item: {"id": str, "instruction": str}.
    """

    __tablename__ = "homework"
    __table_args__ = (Index("ix_homework_user_generated_at", "user_id", "generated_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="RESTRICT"), nullable=False
    )
    tasks: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lesson: Mapped["Lesson"] = relationship()  # noqa: F821
    attempts: Mapped[list["HomeworkAttempt"]] = relationship(
        back_populates="homework", cascade="all, delete-orphan"
    )


class HomeworkAttempt(Base):
    """A learner's submitted answer to one homework task, with AI feedback.

    Reuses the exact feedback shape `AIService.generate_writing_feedback`
    already produces — a homework answer is just English text to give
    feedback on, no separate evaluation prompt needed.
    """

    __tablename__ = "homework_attempts"
    __table_args__ = (Index("ix_homework_attempts_homework", "homework_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    homework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("homework.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[str] = mapped_column(String(64), nullable=False)
    submitted_text: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[dict] = mapped_column(JSONB, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    homework: Mapped["Homework"] = relationship(back_populates="attempts")
