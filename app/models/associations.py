from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

lesson_vocabulary = Table(
    "lesson_vocabulary",
    Base.metadata,
    Column(
        "lesson_id",
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("vocabulary_id", UUID(as_uuid=True), ForeignKey("vocabulary.id"), primary_key=True),
)

lesson_grammar_topics = Table(
    "lesson_grammar_topics",
    Base.metadata,
    Column(
        "lesson_id",
        UUID(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "grammar_topic_id",
        UUID(as_uuid=True),
        ForeignKey("grammar_topics.id"),
        primary_key=True,
    ),
)
