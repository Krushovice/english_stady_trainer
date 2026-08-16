"""Deterministic mistake-status classification.

Pure function, no DB access — CLAUDE.md's Mistake System asks the system
to "distinguish: new mistake, repeated mistake, improving, mastered".
This is the whole rule set, isolated so it stays unit-testable and easy
to retune without touching the service/repository layers around it.
"""

from dataclasses import dataclass

from app.models.user_mistake import MistakeStatus

# Consecutive correct answers on a topic needed to call it "mastered".
MASTERY_STREAK = 3


@dataclass(frozen=True)
class MistakeState:
    status: MistakeStatus
    total_attempts: int
    incorrect_attempts: int
    consecutive_correct: int


def classify_attempt(state: MistakeState | None, is_correct: bool) -> MistakeState | None:
    """Given the topic's current mistake state (None if it has never been

    wrong before) and whether the latest attempt was correct, return the
    new state — or None if there's still nothing to track (no prior
    mistake, and this attempt was correct too).
    """
    if state is None:
        if is_correct:
            return None
        return MistakeState(
            status=MistakeStatus.NEW, total_attempts=1, incorrect_attempts=1, consecutive_correct=0
        )

    total_attempts = state.total_attempts + 1

    if is_correct:
        consecutive_correct = state.consecutive_correct + 1
        status = (
            MistakeStatus.MASTERED
            if consecutive_correct >= MASTERY_STREAK
            else MistakeStatus.IMPROVING
        )
        return MistakeState(
            status=status,
            total_attempts=total_attempts,
            incorrect_attempts=state.incorrect_attempts,
            consecutive_correct=consecutive_correct,
        )

    return MistakeState(
        status=MistakeStatus.REPEATED,
        total_attempts=total_attempts,
        incorrect_attempts=state.incorrect_attempts + 1,
        consecutive_correct=0,
    )
