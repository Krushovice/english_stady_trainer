import uuid

from pydantic import BaseModel, ConfigDict

from app.models.learning_profile import CEFRLevel
from app.models.lesson_block import BlockType


class LevelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: CEFRLevel
    order_index: int
    unlocked: bool


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    order_index: int
    unlocked: bool
    passed: bool | None


class LessonSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    order_index: int


class LessonBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    block_type: BlockType
    order_index: int
    content: dict


class VocabularyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    headword: str
    translation: str
    example_sentence: str
    audio_url: str | None


class GrammarTopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    description: str


class LessonDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    title: str
    order_index: int
    blocks: list[LessonBlockResponse]
    vocabulary: list[VocabularyResponse]
    grammar_topics: list[GrammarTopicResponse]
    next_lesson_slug: str | None = None
