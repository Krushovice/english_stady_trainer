import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CEFRLevel(enum.StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"


cefr_level_type = Enum(CEFRLevel, name="cefr_level")


class LearningProfile(Base):
    """Per-user personalization state: per-skill CEFR level and priority goals.

    This is the multi-user hook described in ARCHITECTURE.md — a future
    second user gets their own row here instead of any code branching on
    "the" user.
    """

    __tablename__ = "learning_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    level_grammar: Mapped[CEFRLevel | None] = mapped_column(cefr_level_type, nullable=True)
    level_vocabulary: Mapped[CEFRLevel | None] = mapped_column(cefr_level_type, nullable=True)
    level_reading: Mapped[CEFRLevel | None] = mapped_column(cefr_level_type, nullable=True)
    level_listening: Mapped[CEFRLevel | None] = mapped_column(cefr_level_type, nullable=True)
    level_speaking: Mapped[CEFRLevel | None] = mapped_column(cefr_level_type, nullable=True)
    level_writing: Mapped[CEFRLevel | None] = mapped_column(cefr_level_type, nullable=True)

    priority_goals: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    placement_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="learning_profile")  # noqa: F821
