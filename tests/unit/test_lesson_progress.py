import uuid
from decimal import Decimal

from app.services.lesson_progress_service import PASS_THRESHOLD, compute_completion


def _ids(n: int) -> list[uuid.UUID]:
    return [uuid.uuid4() for _ in range(n)]


def test_lesson_with_no_exercises_is_auto_passed() -> None:
    completion = compute_completion([], {})
    assert completion.attempted is False
    assert completion.accuracy is None
    assert completion.passed is True
    assert completion.total == 0


def test_never_attempted_lesson_is_not_attempted_or_passed() -> None:
    exercise_ids = _ids(5)
    completion = compute_completion(exercise_ids, {})
    assert completion.attempted is False
    assert completion.accuracy is None
    assert completion.passed is False
    assert completion.wrong_exercise_ids == exercise_ids
    assert completion.correct == 0
    assert completion.total == 5


def test_exactly_at_threshold_passes() -> None:
    exercise_ids = _ids(10)
    # 7/10 = 0.7, exactly PASS_THRESHOLD.
    correctness = {eid: True for eid in exercise_ids[:7]} | {eid: False for eid in exercise_ids[7:]}
    completion = compute_completion(exercise_ids, correctness)
    assert completion.accuracy == PASS_THRESHOLD
    assert completion.passed is True
    assert completion.correct == 7
    assert set(completion.wrong_exercise_ids) == set(exercise_ids[7:])


def test_just_below_threshold_fails() -> None:
    exercise_ids = _ids(10)
    # 6/10 = 0.6, just under PASS_THRESHOLD.
    correctness = {eid: True for eid in exercise_ids[:6]}
    completion = compute_completion(exercise_ids, correctness)
    assert completion.accuracy == Decimal("0.6")
    assert completion.passed is False


def test_unattempted_exercises_count_as_wrong() -> None:
    exercise_ids = _ids(4)
    # Only the first exercise has an attempt at all; the rest were never tried.
    correctness = {exercise_ids[0]: True}
    completion = compute_completion(exercise_ids, correctness)
    assert completion.attempted is True
    assert completion.correct == 1
    assert set(completion.wrong_exercise_ids) == set(exercise_ids[1:])


def test_retry_replacing_a_wrong_answer_with_a_correct_one_can_flip_pass() -> None:
    exercise_ids = _ids(10)
    correctness_before = {eid: True for eid in exercise_ids[:6]}
    assert compute_completion(exercise_ids, correctness_before).passed is False

    correctness_after = {**correctness_before, exercise_ids[6]: True}
    completion_after = compute_completion(exercise_ids, correctness_after)
    assert completion_after.passed is True
    assert completion_after.correct == 7
