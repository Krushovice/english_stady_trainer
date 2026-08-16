import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import lesson_grammar_topics
from app.models.base import Base


class GrammarTopic(Base):
    """A grammar topic, e.g. `present-simple-questions`. Its slug is the key

    mistake tracking (Phase 4) will use to link recurring errors back here.
    """

    __tablename__ = "grammar_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        secondary=lesson_grammar_topics, back_populates="grammar_topics"
    )
