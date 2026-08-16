import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.exercise import Exercise
from app.models.exercise_attempt import AttemptSource, ExerciseAttempt
from app.repositories.exercise_repository import ExerciseRepository, SkillProgress
from app.services.scoring import score_attempt


class ExerciseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExerciseRepository(session)

    async def list_lesson_exercises(self, lesson_slug: str) -> list[Exercise]:
        return list(await self._repo.list_by_lesson_slug(lesson_slug))

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
        await self._session.commit()
        attempt.exercise = exercise
        return attempt

    async def list_attempts(
        self, user_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> list[ExerciseAttempt]:
        return list(await self._repo.list_attempts(user_id, exercise_id))

    async def get_progress(self, user_id: uuid.UUID) -> Sequence[SkillProgress]:
        return await self._repo.get_skill_progress(user_id)
