import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ConversationRole(enum.StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


conversation_role_type = Enum(ConversationRole, name="conversation_role")


class ConversationSession(Base):
    """An open-ended text conversation practice session (CLAUDE.md's "AI
    Conversation").

    `analysis` is null until `ConversationService.end()` runs — a session's
    mistakes/vocabulary/grammar-topics summary, in the same trust-the-shape
    JSONB pattern as `Homework.tasks` and `Exercise.answer_key`.
    """

    __tablename__ = "conversation_sessions"
    __table_args__ = (Index("ix_conversation_sessions_user_started_at", "user_id", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.sequence",
    )


class ConversationMessage(Base):
    """One turn in a conversation session.

    `sequence` (not just `created_at`) orders turns within a session — the
    user+assistant pair from one turn can share the same transaction
    timestamp (Postgres `now()` is transaction-scoped), which would make
    `created_at` alone an unreliable sort key for message order.
    """

    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_session", "session_id"),
        UniqueConstraint(
            "session_id", "sequence", name="uq_conversation_messages_session_sequence"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ConversationRole] = mapped_column(conversation_role_type, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["ConversationSession"] = relationship(back_populates="messages")
