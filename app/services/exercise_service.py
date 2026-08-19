import random
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.exercise import Exercise, Skill
from app.models.exercise_attempt import AttemptSource, ExerciseAttempt
from app.models.review_item import ReviewItemType
from app.repositories.course_repository import CourseRepository
from app.repositories.exercise_repository import ExerciseRepository, SkillProgress
from app.services.mistake_service import MistakeService
from app.services.review_service import ReviewService
from app.services.scoring import score_attempt

DAILY_QUIZ_SIZE = 8


@dataclass(frozen=True)
class MiniTestResult:
    previous_lesson_title: str | None
    exercises: list[Exercise]


class ExerciseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExerciseRepository(session)
        self._course = CourseRepository(session)
        self._mistakes = MistakeService(session)
        self._reviews = ReviewService(session)

    async def list_lesson_exercises(self, lesson_slug: str) -> list[Exercise]:
        return list(await self._repo.list_by_lesson_slug(lesson_slug))

    async def get_mini_test_for_lesson(self, lesson_slug: str) -> MiniTestResult:
        """5-question quick review of the *previous* lesson's topic, shown
        on the current lesson's page — immediate, same-visit reinforcement
        distinct from the next-day spaced-repetition Review Center (which
        can't cover this moment; see docs/decisions.md).
        """
        lesson = await self._course.get_lesson_by_slug(lesson_slug)
        if lesson is None:
            raise NotFoundError(f"Lesson '{lesson_slug}' not found")

        previous_lesson = await self._course.get_previous_lesson_in_level(lesson.id)
        if previous_lesson is None:
            return MiniTestResult(previous_lesson_title=None, exercises=[])

        exercises = list(await self._repo.list_mini_test_by_lesson_id(previous_lesson.id))
        return MiniTestResult(previous_lesson_title=previous_lesson.title, exercises=exercises)

    async def submit_attempt(
        self,
        user_id: uuid.UUID,
        exercise_id: uuid.UUID,
        submitted_answer: dict,
        source: AttemptSource,
    ) -> ExerciseAttempt:
        exercise = await self._repo.get_by_id(exercise_id)
        if exercise is None:
            raise NotFoundError(f"Exercise '{exercise_id}' not found")

        result = score_attempt(exercise, submitted_answer)
        attempt = ExerciseAttempt(
            user_id=user_id,
            exercise_id=exercise_id,
            submitted_answer=submitted_answer,
            is_correct=result.is_correct,
            score=result.score,
            source=source,
        )
        await self._repo.add_attempt(attempt)

        # Every attempt schedules its next review; a grammar-topic-tagged
        # exercise also updates weak-topic mistake tracking. Same
        # transaction as the attempt itself — commit below covers all of it.
        await self._reviews.record_outcome(
            user_id, ReviewItemType.EXERCISE, exercise.id, result.is_correct
        )
        if exercise.vocabulary_id is not None:
            await self._reviews.record_outcome(
                user_id, ReviewItemType.VOCABULARY, exercise.vocabulary_id, result.is_correct
            )
        if exercise.grammar_topic_id is not None:
            await self._reviews.record_outcome(
                user_id, ReviewItemType.GRAMMAR_TOPIC, exercise.grammar_topic_id, result.is_correct
            )
            await self._mistakes.record_attempt(
                user_id, exercise.grammar_topic_id, result.is_correct
            )

        await self._session.commit()
        attempt.exercise = exercise
        return attempt

    async def list_attempts(
        self, user_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> list[ExerciseAttempt]:
        return list(await self._repo.list_attempts(user_id, exercise_id))

    async def get_progress(self, user_id: uuid.UUID) -> Sequence[SkillProgress]:
        return await self._repo.get_skill_progress(user_id)

    async def get_daily_quiz(self, user_id: uuid.UUID, *, today: date) -> list[Exercise]:
        """A quiz mixing exercises across the skills the user has already
        practiced, not a spaced-repetition review queue (see docs/decisions.md
        — the two are deliberately separate features). Stable for the whole
        day: seeded by (user, date) instead of persisted anywhere.
        """
        candidates = list(await self._repo.list_studied_exercises(user_id))
        if not candidates:
            return []

        rng = random.Random(f"{user_id}:{today.isoformat()}")
        rng.shuffle(candidates)

        by_skill: dict[Skill, list[Exercise]] = {}
        for exercise in candidates:
            by_skill.setdefault(exercise.skill, []).append(exercise)

        skills = list(by_skill.keys())
        picked: list[Exercise] = []
        i = 0
        while len(picked) < DAILY_QUIZ_SIZE and any(by_skill.values()):
            skill = skills[i % len(skills)]
            if by_skill[skill]:
                picked.append(by_skill[skill].pop())
            i += 1
        return picked
