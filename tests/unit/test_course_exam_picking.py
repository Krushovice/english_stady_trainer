import uuid

from app.models.exercise import Exercise, ExerciseType, Skill
from app.models.learning_profile import CEFRLevel
from app.services.course_exam_service import _sort_easy_to_hard
from app.services.placement_scoring import LEVEL_ORDER


def _exercise(difficulty: CEFRLevel) -> Exercise:
    return Exercise(
        id=uuid.uuid4(),
        slug=f"ex-{uuid.uuid4().hex[:8]}",
        lesson_id=None,
        exercise_type=ExerciseType.MULTIPLE_CHOICE,
        skill=Skill.GRAMMAR,
        difficulty=difficulty,
        prompt={},
        answer_key={},
        explanation="",
    )


def test_orders_strictly_ascending_by_difficulty_with_no_shuffle_across_tiers() -> None:
    pool = [
        _exercise(CEFRLevel.B2),
        _exercise(CEFRLevel.A1),
        _exercise(CEFRLevel.B1),
        _exercise(CEFRLevel.A2),
        _exercise(CEFRLevel.A1),
    ]
    picked = _sort_easy_to_hard(pool)
    ranks = [LEVEL_ORDER.index(exercise.difficulty) for exercise in picked]
    assert ranks == sorted(ranks)


def test_preserves_the_bank_size_exactly() -> None:
    pool = [_exercise(CEFRLevel.A1) for _ in range(11)] + [
        _exercise(CEFRLevel.B2) for _ in range(11)
    ]
    assert len(_sort_easy_to_hard(pool)) == 22


def test_is_stable_within_a_tier() -> None:
    first, second = _exercise(CEFRLevel.A1), _exercise(CEFRLevel.A1)
    picked = _sort_easy_to_hard([first, second])
    assert picked == [first, second]


def test_empty_pool_returns_empty_list() -> None:
    assert _sort_easy_to_hard([]) == []
