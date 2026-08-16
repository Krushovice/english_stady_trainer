import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import lesson_vocabulary
from app.models.base import Base


class Vocabulary(Base):
    """A single word/phrase. Unique on `headword` so the same item recurring

    across lessons is one row linked to many lessons, not duplicated.
    """

    __tablename__ = "vocabulary"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    headword: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    translation: Mapped[str] = mapped_column(String(255), nullable=False)
    example_sentence: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        secondary=lesson_vocabulary, back_populates="vocabulary"
    )
