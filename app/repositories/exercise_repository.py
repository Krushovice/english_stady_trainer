import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise, ExerciseType, Skill
from app.models.exercise_attempt import AttemptSource, ExerciseAttempt
from app.models.learning_profile import CEFRLevel
from app.models.lesson import Lesson


class SkillProgress:
    __slots__ = ("skill", "attempts_count", "correct_count")

    def __init__(self, skill: Skill, attempts_count: int, correct_count: int) -> None:
        self.skill = skill
        self.attempts_count = attempts_count
        self.correct_count = correct_count


class ExerciseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- writes, used by the content loader ---

    async def upsert_exercise(
        self,
        slug: str,
        lesson_id: uuid.UUID | None,
        exercise_type: ExerciseType,
        skill: Skill,
        difficulty: CEFRLevel,
        prompt: dict,
        answer_key: dict,
        explanation: str,
        grammar_topic_id: uuid.UUID | None,
        vocabulary_id: uuid.UUID | None,
        is_placement_item: bool = False,
    ) -> Exercise:
        exercise = (
            await self._session.execute(select(Exercise).where(Exercise.slug == slug))
        ).scalar_one_or_none()
        if exercise is None:
            exercise = Exercise(slug=slug)
            self._session.add(exercise)

        exercise.lesson_id = lesson_id
        exercise.exercise_type = exercise_type
        exercise.skill = skill
        exercise.difficulty = difficulty
        exercise.prompt = prompt
        exercise.answer_key = answer_key
        exercise.explanation = explanation
        exercise.grammar_topic_id = grammar_topic_id
        exercise.vocabulary_id = vocabulary_id
        exercise.is_placement_item = is_placement_item
        await self._session.flush()
        return exercise

    async def add_attempt(self, attempt: ExerciseAttempt) -> ExerciseAttempt:
        self._session.add(attempt)
        await self._session.flush()
        return attempt

    # --- reads, used by the API ---

    async def get_by_id(self, exercise_id: uuid.UUID) -> Exercise | None:
        return await self._session.get(Exercise, exercise_id)

    async def list_by_lesson_slug(self, lesson_slug: str) -> Sequence[Exercise]:
        result = await self._session.execute(
            select(Exercise).join(Lesson).where(Lesson.slug == lesson_slug).order_by(Exercise.slug)
        )
        return result.scalars().all()

    async def list_placement_items(self) -> Sequence[Exercise]:
        result = await self._session.execute(
            select(Exercise).where(Exercise.is_placement_item.is_(True)).order_by(Exercise.slug)
        )
        return result.scalars().all()

    async def list_attempts(
        self, user_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> Sequence[ExerciseAttempt]:
        result = await self._session.execute(
            select(ExerciseAttempt)
            .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.exercise_id == exercise_id)
            .order_by(ExerciseAttempt.attempted_at.desc())
        )
        return result.scalars().all()

    async def get_most_recently_studied_lesson_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        """Lesson behind the user's most recent non-placement attempt, if any.

        Homework generation reinforces "recently studied material" (CLAUDE.md)
        — this is the concrete definition of "recent": the lesson the user was
        last actually practicing, not just enrolled in.
        """
        result = await self._session.execute(
            select(Exercise.lesson_id)
            .join(ExerciseAttempt, ExerciseAttempt.exercise_id == Exercise.id)
            .where(
                ExerciseAttempt.user_id == user_id,
                ExerciseAttempt.source != AttemptSource.PLACEMENT_TEST,
                Exercise.lesson_id.is_not(None),
            )
            .order_by(ExerciseAttempt.attempted_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_skill_progress(self, user_id: uuid.UUID) -> Sequence[SkillProgress]:
        result = await self._session.execute(
            select(
                Exercise.skill,
                func.count(ExerciseAttempt.id),
                func.count(ExerciseAttempt.id).filter(ExerciseAttempt.is_correct.is_(True)),
            )
            .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
            .where(ExerciseAttempt.user_id == user_id)
            .group_by(Exercise.skill)
            .order_by(Exercise.skill)
        )
        return [
            SkillProgress(skill=skill, attempts_count=attempts_count, correct_count=correct_count)
            for skill, attempts_count, correct_count in result.all()
        ]
