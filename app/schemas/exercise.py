"""Per-exercise-type prompt/answer-key/submission shapes.

Shared by two callers: the content loader validates authored `prompt` and
`answer_key` JSON against these before persisting an exercise, and the
scoring service (`app/services/scoring.py`) parses the same stored JSON
plus a learner's `submitted_answer` through the matching pair before
grading. One definition, so the two can never silently drift apart.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.models.exercise import Skill
from app.models.exercise_attempt import AttemptSource
from app.models.learning_profile import CEFRLevel


class SupportedExerciseType(StrEnum):
    """The subset of `ExerciseType` with a scoring implementation.

    CLAUDE.md: "Start with a small number of exercise types and expand only
    when the abstraction is stable." The DB enum already carries the full
    CLAUDE.md list (see `app/models/exercise.py`); this one gates what
    content authors can actually use today.
    """

    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SENTENCE_ORDERING = "sentence_ordering"
    READING_COMPREHENSION = "reading_comprehension"


class MultipleChoiceOption(BaseModel):
    id: str
    text: str


class MultipleChoicePrompt(BaseModel):
    question: str
    options: list[MultipleChoiceOption]


class MultipleChoiceAnswerKey(BaseModel):
    correct_option_id: str


class MultipleChoiceSubmission(BaseModel):
    option_id: str


class FillBlankPrompt(BaseModel):
    text: str


class FillBlankAnswerKey(BaseModel):
    blanks: list[list[str]]  # one accepted-answers list per blank, in order


class FillBlankSubmission(BaseModel):
    blanks: list[str]


class SentenceOrderingPrompt(BaseModel):
    words: list[str]


class SentenceOrderingAnswerKey(BaseModel):
    correct_order: list[str]


class SentenceOrderingSubmission(BaseModel):
    order: list[str]


class ReadingComprehensionQuestion(BaseModel):
    id: str
    text: str
    options: list[MultipleChoiceOption]


class ReadingComprehensionPrompt(BaseModel):
    passage: str
    questions: list[ReadingComprehensionQuestion]


class ReadingComprehensionAnswerKey(BaseModel):
    answers: dict[str, str]  # question id -> correct option id


class ReadingComprehensionSubmission(BaseModel):
    answers: dict[str, str]


PROMPT_MODELS: dict[SupportedExerciseType, type[BaseModel]] = {
    SupportedExerciseType.MULTIPLE_CHOICE: MultipleChoicePrompt,
    SupportedExerciseType.FILL_BLANK: FillBlankPrompt,
    SupportedExerciseType.SENTENCE_ORDERING: SentenceOrderingPrompt,
    SupportedExerciseType.READING_COMPREHENSION: ReadingComprehensionPrompt,
}

ANSWER_KEY_MODELS: dict[SupportedExerciseType, type[BaseModel]] = {
    SupportedExerciseType.MULTIPLE_CHOICE: MultipleChoiceAnswerKey,
    SupportedExerciseType.FILL_BLANK: FillBlankAnswerKey,
    SupportedExerciseType.SENTENCE_ORDERING: SentenceOrderingAnswerKey,
    SupportedExerciseType.READING_COMPREHENSION: ReadingComprehensionAnswerKey,
}

SUBMISSION_MODELS: dict[SupportedExerciseType, type[BaseModel]] = {
    SupportedExerciseType.MULTIPLE_CHOICE: MultipleChoiceSubmission,
    SupportedExerciseType.FILL_BLANK: FillBlankSubmission,
    SupportedExerciseType.SENTENCE_ORDERING: SentenceOrderingSubmission,
    SupportedExerciseType.READING_COMPREHENSION: ReadingComprehensionSubmission,
}


# --- API request/response shapes ---


class ExercisePublicResponse(BaseModel):
    """What a learner sees before attempting — no answer_key, no explanation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    exercise_type: SupportedExerciseType
    skill: Skill
    difficulty: CEFRLevel
    prompt: dict


class SubmitAttemptRequest(BaseModel):
    submitted_answer: dict
    source: AttemptSource = AttemptSource.LESSON_PRACTICE


class AttemptResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_correct: bool
    score: Decimal
    explanation: str
    answer_key: dict
    attempted_at: datetime


class AttemptHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submitted_answer: dict
    is_correct: bool
    score: Decimal | None
    source: AttemptSource
    attempted_at: datetime


class SkillProgressResponse(BaseModel):
    skill: Skill
    attempts_count: int
    correct_count: int
    accuracy: Decimal
