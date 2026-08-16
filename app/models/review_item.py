import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ReviewItemType(enum.StrEnum):
    VOCABULARY = "vocabulary"
    GRAMMAR_TOPIC = "grammar_topic"
    EXERCISE = "exercise"


review_item_type_type = Enum(ReviewItemType, name="review_item_type")


class ReviewItem(Base):
    """A single spaced-repetition queue entry for one user.

    Polymorphic over what's being reviewed — exactly one of
    vocabulary_id/grammar_topic_id/exercise_id is set, matching
    `item_type` (enforced by the service layer, not a DB constraint).
    Covers CLAUDE.md's "vocabulary; phrases; grammar patterns; mistakes;
    exercises where the user performed poorly" in one table rather than
    three near-identical ones. Scheduling fields (interval/ease/due_at)
    follow `app/services/spaced_repetition.py`; also doubles as the
    per-word "mastery" signal the roadmap calls `UserVocabulary` — see
    docs/decisions.md for why that's not a separate table.
    """

    __tablename__ = "review_items"
    __table_args__ = (
        Index(
            "uq_review_items_user_vocabulary",
            "user_id",
            "vocabulary_id",
            unique=True,
            postgresql_where=text("vocabulary_id IS NOT NULL"),
        ),
        Index(
            "uq_review_items_user_grammar_topic",
            "user_id",
            "grammar_topic_id",
            unique=True,
            postgresql_where=text("grammar_topic_id IS NOT NULL"),
        ),
        Index(
            "uq_review_items_user_exercise",
            "user_id",
            "exercise_id",
            unique=True,
            postgresql_where=text("exercise_id IS NOT NULL"),
        ),
        Index("ix_review_items_user_due", "user_id", "due_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    item_type: Mapped[ReviewItemType] = mapped_column(review_item_type_type, nullable=False)
    vocabulary_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=True
    )
    grammar_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grammar_topics.id", ondelete="CASCADE"), nullable=True
    )
    exercise_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=True
    )

    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ease_factor: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, default=Decimal("2.5")
    )
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vocabulary: Mapped["Vocabulary | None"] = relationship()  # noqa: F821
    grammar_topic: Mapped["GrammarTopic | None"] = relationship()  # noqa: F821
    exercise: Mapped["Exercise | None"] = relationship()  # noqa: F821
