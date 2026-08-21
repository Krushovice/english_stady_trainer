import uuid

from app.models.exercise import Exercise, ExerciseType, Skill
from app.models.learning_profile import CEFRLevel
from app.services.course_exam_service import _pick_easy_to_hard
from app.services.placement_scoring import LEVEL_ORDER


def _exercise(difficulty: CEFRLevel, lesson_id: uuid.UUID | None = None) -> Exercise:
    return Exercise(
        id=uuid.uuid4(),
        slug=f"ex-{uuid.uuid4().hex[:8]}",
        lesson_id=lesson_id or uuid.uuid4(),
        exercise_type=ExerciseType.MULTIPLE_CHOICE,
        skill=Skill.GRAMMAR,
        difficulty=difficulty,
        prompt={},
        answer_key={},
        explanation="",
    )


def _pool(counts: dict[CEFRLevel, int]) -> list[Exercise]:
    pool: list[Exercise] = []
    for level, count in counts.items():
        for _ in range(count):
            pool.append(_exercise(level))
    return pool


def test_even_split_across_four_difficulty_buckets() -> None:
    pool = _pool({CEFRLevel.A1: 20, CEFRLevel.A2: 20, CEFRLevel.B1: 20, CEFRLevel.B2: 20})
    picked = _pick_easy_to_hard(pool, 44)
    assert len(picked) == 44
    counts = {level: 0 for level in LEVEL_ORDER}
    for exercise in picked:
        counts[exercise.difficulty] += 1
    assert counts == {CEFRLevel.A1: 11, CEFRLevel.A2: 11, CEFRLevel.B1: 11, CEFRLevel.B2: 11}


def test_output_is_strictly_ascending_by_difficulty_with_no_shuffle_across_tiers() -> None:
    pool = _pool({CEFRLevel.A1: 15, CEFRLevel.A2: 15, CEFRLevel.B1: 15, CEFRLevel.B2: 15})
    picked = _pick_easy_to_hard(pool, 40)
    ranks = [LEVEL_ORDER.index(exercise.difficulty) for exercise in picked]
    assert ranks == sorted(ranks)


def test_remainder_is_distributed_to_earlier_buckets() -> None:
    pool = _pool({CEFRLevel.A1: 20, CEFRLevel.A2: 20, CEFRLevel.B1: 20, CEFRLevel.B2: 20})
    picked = _pick_easy_to_hard(pool, 41)  # 41 // 4 = 10, remainder 1 -> A1 gets 11
    counts = {level: 0 for level in LEVEL_ORDER}
    for exercise in picked:
        counts[exercise.difficulty] += 1
    assert counts == {CEFRLevel.A1: 11, CEFRLevel.A2: 10, CEFRLevel.B1: 10, CEFRLevel.B2: 10}


def test_thin_bucket_returns_fewer_total_picks_without_crashing() -> None:
    pool = _pool({CEFRLevel.A1: 20, CEFRLevel.A2: 2, CEFRLevel.B1: 20, CEFRLevel.B2: 20})
    picked = _pick_easy_to_hard(pool, 44)
    counts = {level: 0 for level in LEVEL_ORDER}
    for exercise in picked:
        counts[exercise.difficulty] += 1
    assert counts[CEFRLevel.A2] == 2  # short of its 11-item share, not redistributed
    assert len(picked) == 44 - (11 - 2)


def test_empty_pool_returns_empty_list() -> None:
    assert _pick_easy_to_hard([], 44) == []
