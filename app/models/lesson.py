import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import lesson_grammar_topics, lesson_vocabulary
from app.models.base import Base


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("module_id", "order_index", name="uq_lessons_module_order"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modules.id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_path: Mapped[str] = mapped_column(Text, nullable=False)

    module: Mapped["Module"] = relationship(back_populates="lessons")  # noqa: F821
    blocks: Mapped[list["LessonBlock"]] = relationship(  # noqa: F821
        back_populates="lesson", order_by="LessonBlock.order_index", cascade="all, delete-orphan"
    )
    vocabulary: Mapped[list["Vocabulary"]] = relationship(  # noqa: F821
        secondary=lesson_vocabulary, back_populates="lessons"
    )
    grammar_topics: Mapped[list["GrammarTopic"]] = relationship(  # noqa: F821
        secondary=lesson_grammar_topics, back_populates="lessons"
    )
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="lesson")  # noqa: F821
