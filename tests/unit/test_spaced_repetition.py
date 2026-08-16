from datetime import UTC, datetime
from decimal import Decimal

from app.services.spaced_repetition import (
    DEFAULT_EASE_FACTOR,
    MIN_EASE_FACTOR,
    ReviewState,
    schedule_next_review,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _new_state() -> ReviewState:
    return ReviewState(interval_days=0, ease_factor=DEFAULT_EASE_FACTOR, review_count=0)


def test_first_correct_review_schedules_one_day_out() -> None:
    state, due_at = schedule_next_review(_new_state(), is_correct=True, now=NOW)
    assert state.interval_days == 1
    assert due_at == NOW.replace(day=2)
    assert state.review_count == 1


def test_second_correct_review_schedules_six_days_out() -> None:
    state, _ = schedule_next_review(_new_state(), is_correct=True, now=NOW)
    state, due_at = schedule_next_review(state, is_correct=True, now=NOW)
    assert state.interval_days == 6
    assert state.review_count == 2


def test_third_correct_review_multiplies_by_ease_factor() -> None:
    state = ReviewState(interval_days=6, ease_factor=Decimal("2.5"), review_count=2)
    new_state, _ = schedule_next_review(state, is_correct=True, now=NOW)
    assert new_state.interval_days == 15  # round(6 * 2.5)
    assert new_state.review_count == 3


def test_ease_factor_increases_on_correct_review() -> None:
    state, _ = schedule_next_review(_new_state(), is_correct=True, now=NOW)
    assert state.ease_factor == DEFAULT_EASE_FACTOR + Decimal("0.1")


def test_incorrect_review_resets_interval_and_count() -> None:
    state = ReviewState(interval_days=15, ease_factor=Decimal("2.6"), review_count=3)
    new_state, due_at = schedule_next_review(state, is_correct=False, now=NOW)
    assert new_state.interval_days == 1
    assert new_state.review_count == 0
    assert due_at == NOW.replace(day=2)


def test_ease_factor_decreases_on_incorrect_review_but_has_a_floor() -> None:
    state = ReviewState(interval_days=1, ease_factor=MIN_EASE_FACTOR, review_count=0)
    new_state, _ = schedule_next_review(state, is_correct=False, now=NOW)
    assert new_state.ease_factor == MIN_EASE_FACTOR  # already at floor, doesn't go lower
