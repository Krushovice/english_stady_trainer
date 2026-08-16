import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MistakeStatus(enum.StrEnum):
    NEW = "new"
    REPEATED = "repeated"
    IMPROVING = "improving"
    MASTERED = "mastered"


mistake_status_type = Enum(MistakeStatus, name="mistake_status")


class UserMistake(Base):  # noqa: F821
    """Persistent per-user, per-grammar-topic mistake tracking.

    Scoped to grammar topics only — vocabulary recall is tracked instead
    by spaced-repetition review state (`ReviewItem`), not duplicated here.
    `error_rate` (incorrect_attempts / total_attempts) is derived, not
    stored, to avoid two numbers that can drift out of sync.
    """

    __tablename__ = "user_mistakes"
    __table_args__ = (
        UniqueConstraint("user_id", "grammar_topic_id", name="uq_user_mistakes_user_topic"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    grammar_topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grammar_topics.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[MistakeStatus] = mapped_column(
        mistake_status_type, nullable=False, default=MistakeStatus.NEW
    )
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incorrect_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    grammar_topic: Mapped["GrammarTopic"] = relationship()  # noqa: F821
