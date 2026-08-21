"""Sequential lesson gating within a level: a lesson unlocks only once the
lesson immediately before it (in authoring order) has been passed.

Product ask (2026-08-21, live-testing feedback): lessons inside a level
could previously be opened in any order. 70% correct on a lesson's own
exercises is the threshold that unlocks the next one; short of that, the
unresolved exercises should stay visible on revisit rather than being
silently dropped (see `LessonPage.tsx`'s completion banner).
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.repositories.course_repository import CourseRepository
from app.repositories.exercise_repository import ExerciseRepository

PASS_THRESHOLD = Decimal("0.7")


@dataclass(frozen=True)
class LessonCompletion:
    attempted: bool
    accuracy: Decimal | None
    passed: bool
    wrong_exercise_ids: list[uuid.UUID]
    total: int
    correct: int


def compute_completion(
    exercise_ids: list[uuid.UUID], correctness: dict[uuid.UUID, bool]
) -> LessonCompletion:
    """Pure scoring step, split out from `get_completion` so the 70%
    threshold logic is unit-testable without a database session — same
    reasoning as `app/services/scoring.py`.

    `correctness` maps an exercise id to whether its *latest* attempt (if
    any) was correct; an id absent from it means "never attempted".
    """
    total = len(exercise_ids)
    if total == 0:
        # Nothing to grade — never block progression on missing content.
        return LessonCompletion(
            attempted=False, accuracy=None, passed=True, wrong_exercise_ids=[], total=0, correct=0
        )

    attempted = bool(correctness)
    correct = sum(1 for is_correct in correctness.values() if is_correct)
    wrong_exercise_ids = [
        exercise_id for exercise_id in exercise_ids if not correctness.get(exercise_id, False)
    ]
    accuracy = Decimal(correct) / Decimal(total) if attempted else None
    passed = accuracy is not None and accuracy >= PASS_THRESHOLD
    return LessonCompletion(
        attempted=attempted,
        accuracy=accuracy,
        passed=passed,
        wrong_exercise_ids=wrong_exercise_ids,
        total=total,
        correct=correct,
    )


class LessonProgressService:
    def __init__(self, session: AsyncSession) -> None:
        self._course = CourseRepository(session)
        self._exercises = ExerciseRepository(session)

    async def get_completion(self, user_id: uuid.UUID, lesson_slug: str) -> LessonCompletion:
        exercises = list(await self._exercises.list_by_lesson_slug(lesson_slug))
        exercise_ids = [exercise.id for exercise in exercises]
        latest = await self._exercises.get_latest_attempts(user_id, exercise_ids)
        correctness = {exercise_id: attempt.is_correct for exercise_id, attempt in latest.items()}
        return compute_completion(exercise_ids, correctness)

    async def is_lesson_unlocked(self, user_id: uuid.UUID, lesson: Lesson) -> bool:
        previous = await self._course.get_previous_lesson_in_level(lesson.id)
        if previous is None:
            return True
        completion = await self.get_completion(user_id, previous.slug)
        return completion.passed
