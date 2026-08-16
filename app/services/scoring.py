"""Deterministic scoring for exercise attempts.

No LLM involved — every supported exercise type is graded by comparing
the learner's submission to the authored `answer_key`. Pure functions,
no DB access, so this is unit-testable in isolation from everything else.
"""

from decimal import Decimal
from typing import NamedTuple

from pydantic import ValidationError

from app.core.exceptions import DomainError
from app.models.exercise import Exercise, ExerciseType
from app.schemas.exercise import (
    FillBlankAnswerKey,
    FillBlankSubmission,
    MultipleChoiceAnswerKey,
    MultipleChoiceSubmission,
    ReadingComprehensionAnswerKey,
    ReadingComprehensionSubmission,
    SentenceOrderingAnswerKey,
    SentenceOrderingSubmission,
)


class InvalidSubmissionError(DomainError):
    """The submitted_answer doesn't match what this exercise expects."""


class ScoringResult(NamedTuple):
    is_correct: bool
    score: Decimal


def score_attempt(exercise: Exercise, submitted_answer: dict) -> ScoringResult:
    scorer = _SCORERS.get(exercise.exercise_type)
    if scorer is None:
        raise InvalidSubmissionError(
            f"Scoring is not implemented for exercise type '{exercise.exercise_type}'"
        )
    try:
        return scorer(exercise.answer_key, submitted_answer)
    except ValidationError as exc:
        raise InvalidSubmissionError(
            "submitted_answer does not match this exercise's expected shape"
        ) from exc


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _score_multiple_choice(answer_key: dict, submitted_answer: dict) -> ScoringResult:
    key = MultipleChoiceAnswerKey.model_validate(answer_key)
    submission = MultipleChoiceSubmission.model_validate(submitted_answer)
    is_correct = submission.option_id == key.correct_option_id
    return ScoringResult(is_correct=is_correct, score=Decimal(1) if is_correct else Decimal(0))


def _score_fill_blank(answer_key: dict, submitted_answer: dict) -> ScoringResult:
    key = FillBlankAnswerKey.model_validate(answer_key)
    submission = FillBlankSubmission.model_validate(submitted_answer)
    if len(submission.blanks) != len(key.blanks):
        raise InvalidSubmissionError("submitted blank count does not match this exercise")

    correct = sum(
        1
        for given, accepted in zip(submission.blanks, key.blanks, strict=True)
        if _normalize(given) in {_normalize(answer) for answer in accepted}
    )
    score = Decimal(correct) / Decimal(len(key.blanks))
    return ScoringResult(is_correct=score == 1, score=score)


def _score_sentence_ordering(answer_key: dict, submitted_answer: dict) -> ScoringResult:
    key = SentenceOrderingAnswerKey.model_validate(answer_key)
    submission = SentenceOrderingSubmission.model_validate(submitted_answer)
    if len(submission.order) != len(key.correct_order):
        raise InvalidSubmissionError("submitted order length does not match this exercise")

    correct_positions = sum(
        1
        for given, expected in zip(submission.order, key.correct_order, strict=True)
        if given == expected
    )
    score = Decimal(correct_positions) / Decimal(len(key.correct_order))
    return ScoringResult(is_correct=score == 1, score=score)


def _score_reading_comprehension(answer_key: dict, submitted_answer: dict) -> ScoringResult:
    key = ReadingComprehensionAnswerKey.model_validate(answer_key)
    submission = ReadingComprehensionSubmission.model_validate(submitted_answer)

    correct = sum(
        1
        for question_id, correct_option_id in key.answers.items()
        if submission.answers.get(question_id) == correct_option_id
    )
    score = Decimal(correct) / Decimal(len(key.answers))
    return ScoringResult(is_correct=score == 1, score=score)


_SCORERS = {
    ExerciseType.MULTIPLE_CHOICE: _score_multiple_choice,
    ExerciseType.FILL_BLANK: _score_fill_blank,
    ExerciseType.SENTENCE_ORDERING: _score_sentence_ordering,
    ExerciseType.READING_COMPREHENSION: _score_reading_comprehension,
}
