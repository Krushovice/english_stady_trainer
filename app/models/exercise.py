import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.learning_profile import CEFRLevel, cefr_level_type


class ExerciseType(enum.StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    FILL_BLANK = "fill_blank"
    SENTENCE_ORDERING = "sentence_ordering"
    MATCHING = "matching"
    TRANSLATION = "translation"
    ERROR_CORRECTION = "error_correction"
    READING_COMPREHENSION = "reading_comprehension"
    LISTENING_COMPREHENSION = "listening_comprehension"
    DICTATION = "dictation"
    WRITING = "writing"
    SPEAKING = "speaking"


class Skill(enum.StrEnum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    READING = "reading"
    LISTENING = "listening"
    WRITING = "writing"
    SPEAKING = "speaking"


exercise_type_type = Enum(ExerciseType, name="exercise_type")
skill_type = Enum(Skill, name="skill")


class Exercise(Base):
    """`slug` is not in the Phase 0 schema proposal; added so the content

    loader can upsert exercises idempotently by natural key, the same way
    it already does for vocabulary (headword) and grammar topics (slug).
    """

    __tablename__ = "exercises"
    __table_args__ = (Index("ix_exercises_skill_difficulty", "skill", "difficulty"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    exercise_type: Mapped[ExerciseType] = mapped_column(exercise_type_type, nullable=False)
    skill: Mapped[Skill] = mapped_column(skill_type, nullable=False)
    difficulty: Mapped[CEFRLevel] = mapped_column(cefr_level_type, nullable=False)
    prompt: Mapped[dict] = mapped_column(JSONB, nullable=False)
    answer_key: Mapped[dict] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    grammar_topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grammar_topics.id", ondelete="SET NULL"), nullable=True
    )
    vocabulary_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vocabulary.id", ondelete="SET NULL"), nullable=True
    )
    is_placement_item: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_mini_test_item: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_final_exam_item: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    lesson: Mapped["Lesson | None"] = relationship(back_populates="exercises")  # noqa: F821
    grammar_topic: Mapped["GrammarTopic | None"] = relationship()  # noqa: F821
    vocabulary: Mapped["Vocabulary | None"] = relationship()  # noqa: F821
    attempts: Mapped[list["ExerciseAttempt"]] = relationship(  # noqa: F821
        back_populates="exercise", cascade="all, delete-orphan"
    )
