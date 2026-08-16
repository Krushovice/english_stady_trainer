"""Validation schemas for course content authored as YAML under `content/`.

These are separate from `app/schemas/course.py` (API response shapes) —
this file validates what an author writes, that file validates what the
API returns.
"""

from pydantic import BaseModel, model_validator

from app.models.exercise import Skill
from app.models.learning_profile import CEFRLevel
from app.models.lesson_block import BlockType
from app.schemas.exercise import ANSWER_KEY_MODELS, PROMPT_MODELS, SupportedExerciseType


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


class ExerciseContent(BaseModel):
    slug: str
    type: SupportedExerciseType
    skill: Skill
    difficulty: CEFRLevel
    prompt: dict
    answer_key: dict
    explanation: str
    grammar_topic_slug: str | None = None
    vocabulary_headword: str | None = None

    @model_validator(mode="after")
    def _validate_prompt_and_answer_key_shape(self) -> "ExerciseContent":
        PROMPT_MODELS[self.type].model_validate(self.prompt)
        ANSWER_KEY_MODELS[self.type].model_validate(self.answer_key)
        return self


class LessonBlockContent(BaseModel):
    type: BlockType
    order_index: int
    content: dict


class LessonFile(BaseModel):
    level: LevelContent
    module: ModuleContent
    lesson: LessonMeta
    blocks: list[LessonBlockContent]
