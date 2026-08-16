"""Deterministic spaced-repetition scheduling.

A simplified SM-2 (SuperMemo 2) variant adapted to a binary correct/
incorrect outcome instead of SM-2's 0-5 quality scale, since exercise
grading here is boolean (`ExerciseAttempt.is_correct`). Pure function, no
DB access — CLAUDE.md: "the scheduling algorithm should be isolated from
UI and API code so it can be changed later."
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

MIN_EASE_FACTOR = Decimal("1.3")
DEFAULT_EASE_FACTOR = Decimal("2.5")
EASE_INCREMENT = Decimal("0.1")
EASE_PENALTY = Decimal("0.2")
FIRST_INTERVAL_DAYS = 1
SECOND_INTERVAL_DAYS = 6


@dataclass(frozen=True)
class ReviewState:
    interval_days: int
    ease_factor: Decimal
    review_count: int


def schedule_next_review(
    state: ReviewState, is_correct: bool, now: datetime
) -> tuple[ReviewState, datetime]:
    """Returns the item's new scheduling state and when it's next due.

    Correct: interval grows (1 day -> 6 days -> interval * ease_factor),
    ease_factor nudges up. Incorrect: resets to a 1-day interval and the
    ease_factor drops — never below MIN_EASE_FACTOR, matching SM-2.
    """
    if not is_correct:
        new_state = ReviewState(
            interval_days=FIRST_INTERVAL_DAYS,
            ease_factor=max(MIN_EASE_FACTOR, state.ease_factor - EASE_PENALTY),
            review_count=0,
        )
    else:
        review_count = state.review_count + 1
        if review_count == 1:
            interval_days = FIRST_INTERVAL_DAYS
        elif review_count == 2:
            interval_days = SECOND_INTERVAL_DAYS
        else:
            interval_days = max(
                SECOND_INTERVAL_DAYS, round(state.interval_days * float(state.ease_factor))
            )
        new_state = ReviewState(
            interval_days=interval_days,
            ease_factor=state.ease_factor + EASE_INCREMENT,
            review_count=review_count,
        )

    due_at = now + timedelta(days=new_state.interval_days)
    return new_state, due_at
