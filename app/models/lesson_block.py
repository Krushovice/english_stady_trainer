import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BlockType(enum.StrEnum):
    LEARNING_GOALS = "learning_goals"
    CONTEXT = "context"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    EXAMPLES = "examples"
    EXERCISES = "exercises"
    MINI_TEST = "mini_test"
    READING = "reading"
    LISTENING = "listening"
    SPEAKING = "speaking"
    HOMEWORK = "homework"
    REVIEW = "review"


block_type_type = Enum(BlockType, name="lesson_block_type")


class LessonBlock(Base):
    """One block inside a lesson. `content` shape depends on `block_type` and

    is validated by the content loader at load time, not by the database.
    """

    __tablename__ = "lesson_blocks"
    __table_args__ = (
        UniqueConstraint("lesson_id", "order_index", name="uq_lesson_blocks_lesson_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    block_type: Mapped[BlockType] = mapped_column(block_type_type, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)

    lesson: Mapped["Lesson"] = relationship(back_populates="blocks")  # noqa: F821
