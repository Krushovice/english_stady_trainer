"""Validation schemas for course content authored as YAML under `content/`.

These are separate from `app/schemas/course.py` (API response shapes) —
this file validates what an author writes, that file validates what the
API returns.
"""

from pydantic import BaseModel

from app.models.learning_profile import CEFRLevel
from app.models.lesson_block import BlockType


class LevelContent(BaseModel):
    code: CEFRLevel
    order_index: int


class ModuleContent(BaseModel):
    slug: str
    title: str
    order_index: int


class LessonMeta(BaseModel):
    slug: str
    title: str
    order_index: int


class VocabularyItem(BaseModel):
    headword: str
    translation: str
    example_sentence: str
    audio_url: str | None = None


class GrammarTopicItem(BaseModel):
    slug: str
    title: str
    description: str


class LessonBlockContent(BaseModel):
    type: BlockType
    order_index: int
    content: dict


class LessonFile(BaseModel):
    level: LevelContent
    module: ModuleContent
    lesson: LessonMeta
    blocks: list[LessonBlockContent]
