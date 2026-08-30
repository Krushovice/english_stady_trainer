from decimal import Decimal

import pytest

from app.models.exercise import Exercise, ExerciseType, Skill
from app.models.learning_profile import CEFRLevel
from app.services.scoring import InvalidSubmissionError, score_attempt


def _exercise(exercise_type: ExerciseType, prompt: dict, answer_key: dict) -> Exercise:
    return Exercise(
        slug="test-exercise",
        exercise_type=exercise_type,
        skill=Skill.GRAMMAR,
        difficulty=CEFRLevel.B1,
        prompt=prompt,
        answer_key=answer_key,
        explanation="because",
    )


def test_multiple_choice_correct() -> None:
    exercise = _exercise(
        ExerciseType.MULTIPLE_CHOICE,
        prompt={
            "question": "2 + 2?",
            "options": [{"id": "a", "text": "3"}, {"id": "b", "text": "4"}],
        },
        answer_key={"correct_option_id": "b"},
    )
    result = score_attempt(exercise, {"option_id": "b"})
    assert result.is_correct is True
    assert result.score == Decimal(1)


def test_multiple_choice_incorrect() -> None:
    exercise = _exercise(
        ExerciseType.MULTIPLE_CHOICE,
        prompt={
            "question": "2 + 2?",
            "options": [{"id": "a", "text": "3"}, {"id": "b", "text": "4"}],
        },
        answer_key={"correct_option_id": "b"},
    )
    result = score_attempt(exercise, {"option_id": "a"})
    assert result.is_correct is False
    assert result.score == Decimal(0)


def test_fill_blank_normalizes_case_and_whitespace() -> None:
    exercise = _exercise(
        ExerciseType.FILL_BLANK,
        prompt={"text": "You work in IT, ___ you?"},
        answer_key={"blanks": [["don't"]]},
    )
    result = score_attempt(exercise, {"blanks": ["  Don't  "]})
    assert result.is_correct is True
    assert result.score == Decimal(1)


def test_fill_blank_partial_credit_across_multiple_blanks() -> None:
    exercise = _exercise(
        ExerciseType.FILL_BLANK,
        prompt={"text": "It's a nice day, ___ it? You haven't been here before, ___ you?"},
        answer_key={"blanks": [["isn't"], ["have"]]},
    )
    result = score_attempt(exercise, {"blanks": ["isn't", "wrong"]})
    assert result.is_correct is False
    assert result.score == Decimal("0.5")


def test_fill_blank_accepts_any_of_several_variants() -> None:
    exercise = _exercise(
        ExerciseType.FILL_BLANK,
        prompt={"text": "I ___ to school."},
        answer_key={"blanks": [["go", "walk"]]},
    )
    result = score_attempt(exercise, {"blanks": ["walk"]})
    assert result.is_correct is True


def test_fill_blank_rejects_wrong_blank_count() -> None:
    exercise = _exercise(
        ExerciseType.FILL_BLANK,
        prompt={"text": "..."},
        answer_key={"blanks": [["a"], ["b"]]},
    )
    with pytest.raises(InvalidSubmissionError):
        score_attempt(exercise, {"blanks": ["a"]})


def test_sentence_ordering_exact_match() -> None:
    exercise = _exercise(
        ExerciseType.SENTENCE_ORDERING,
        prompt={"words": ["is", "This", "a", "test"]},
        answer_key={"correct_order": ["This", "is", "a", "test"]},
    )
    result = score_attempt(exercise, {"order": ["This", "is", "a", "test"]})
    assert result.is_correct is True
    assert result.score == Decimal(1)


def test_sentence_ordering_partial_credit_by_position() -> None:
    exercise = _exercise(
        ExerciseType.SENTENCE_ORDERING,
        prompt={"words": ["is", "This", "a", "test"]},
        answer_key={"correct_order": ["This", "is", "a", "test"]},
    )
    result = score_attempt(exercise, {"order": ["This", "a", "is", "test"]})
    assert result.is_correct is False
    assert result.score == Decimal("0.5")  # positions 0 and 3 correct out of 4


def test_reading_comprehension_partial_credit() -> None:
    exercise = _exercise(
        ExerciseType.READING_COMPREHENSION,
        prompt={"passage": "...", "questions": []},
        answer_key={"answers": {"q1": "a", "q2": "b"}},
    )
    result = score_attempt(exercise, {"answers": {"q1": "a", "q2": "wrong"}})
    assert result.is_correct is False
    assert result.score == Decimal("0.5")


def test_listening_comprehension_scores_like_reading_comprehension() -> None:
    # Same answers-dict shape, only the prompt differs (audio_url instead
    # of passage) — scoring is intentionally the exact same function.
    exercise = _exercise(
        ExerciseType.LISTENING_COMPREHENSION,
        prompt={"audio_url": "/audio/test.mp3", "transcript": "...", "questions": []},
        answer_key={"answers": {"q1": "a", "q2": "b"}},
    )
    result = score_attempt(exercise, {"answers": {"q1": "a", "q2": "b"}})
    assert result.is_correct is True
    assert result.score == Decimal(1)


def test_translation_normalizes_case_whitespace_and_trailing_punctuation() -> None:
    exercise = _exercise(
        ExerciseType.TRANSLATION,
        prompt={"text": "Сколько это стоит?"},
        answer_key={"accepted": ["how much is it", "how much does it cost"]},
    )
    result = score_attempt(exercise, {"text": "  How much IS it?  "})
    assert result.is_correct is True
    assert result.score == Decimal(1)


def test_translation_rejects_an_unlisted_answer() -> None:
    exercise = _exercise(
        ExerciseType.TRANSLATION,
        prompt={"text": "Сколько это стоит?"},
        answer_key={"accepted": ["how much is it"]},
    )
    result = score_attempt(exercise, {"text": "what is the price"})
    assert result.is_correct is False
    assert result.score == Decimal(0)


def test_malformed_submission_raises_invalid_submission_error() -> None:
    exercise = _exercise(
        ExerciseType.MULTIPLE_CHOICE,
        prompt={"question": "?", "options": []},
        answer_key={"correct_option_id": "a"},
    )
    with pytest.raises(InvalidSubmissionError):
        score_attempt(exercise, {"not_the_right_field": "a"})


def test_unsupported_exercise_type_raises_invalid_submission_error() -> None:
    exercise = _exercise(ExerciseType.SPEAKING, prompt={}, answer_key={})
    with pytest.raises(InvalidSubmissionError):
        score_attempt(exercise, {})
