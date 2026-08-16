from app.models.user_mistake import MistakeStatus
from app.services.mistake_classification import MistakeState, classify_attempt


def test_correct_answer_with_no_prior_mistake_tracks_nothing() -> None:
    assert classify_attempt(None, is_correct=True) is None


def test_first_incorrect_answer_is_new() -> None:
    state = classify_attempt(None, is_correct=False)
    assert state == MistakeState(
        status=MistakeStatus.NEW, total_attempts=1, incorrect_attempts=1, consecutive_correct=0
    )


def test_second_incorrect_answer_becomes_repeated() -> None:
    state = MistakeState(
        status=MistakeStatus.NEW, total_attempts=1, incorrect_attempts=1, consecutive_correct=0
    )
    new_state = classify_attempt(state, is_correct=False)
    assert new_state.status == MistakeStatus.REPEATED
    assert new_state.total_attempts == 2
    assert new_state.incorrect_attempts == 2
    assert new_state.consecutive_correct == 0


def test_correct_answer_after_mistake_becomes_improving() -> None:
    state = MistakeState(
        status=MistakeStatus.NEW, total_attempts=1, incorrect_attempts=1, consecutive_correct=0
    )
    new_state = classify_attempt(state, is_correct=True)
    assert new_state.status == MistakeStatus.IMPROVING
    assert new_state.consecutive_correct == 1


def test_three_consecutive_correct_answers_become_mastered() -> None:
    state = MistakeState(
        status=MistakeStatus.NEW, total_attempts=1, incorrect_attempts=1, consecutive_correct=0
    )
    for _ in range(3):
        state = classify_attempt(state, is_correct=True)
    assert state.status == MistakeStatus.MASTERED
    assert state.consecutive_correct == 3


def test_mistake_after_mastery_reverts_to_repeated_not_new() -> None:
    mastered = MistakeState(
        status=MistakeStatus.MASTERED, total_attempts=4, incorrect_attempts=1, consecutive_correct=3
    )
    new_state = classify_attempt(mastered, is_correct=False)
    assert new_state.status == MistakeStatus.REPEATED
    assert new_state.consecutive_correct == 0
    assert new_state.incorrect_attempts == 2


def test_incorrect_answer_resets_consecutive_correct_streak() -> None:
    state = MistakeState(
        status=MistakeStatus.IMPROVING,
        total_attempts=2,
        incorrect_attempts=1,
        consecutive_correct=1,
    )
    new_state = classify_attempt(state, is_correct=False)
    assert new_state.consecutive_correct == 0
    assert new_state.status == MistakeStatus.REPEATED
