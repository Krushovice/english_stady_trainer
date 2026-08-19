import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_profile import CEFRLevel
from app.models.level_exam_attempt import LevelExamAttempt


class LevelExamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, attempt: LevelExamAttempt) -> LevelExamAttempt:
        self._session.add(attempt)
        await self._session.flush()
        return attempt

    async def get_by_id(self, attempt_id: uuid.UUID) -> LevelExamAttempt | None:
        return await self._session.get(LevelExamAttempt, attempt_id)

    async def list_recent(
        self, user_id: uuid.UUID, level: CEFRLevel, *, limit: int
    ) -> Sequence[LevelExamAttempt]:
        result = await self._session.execute(
            select(LevelExamAttempt)
            .where(LevelExamAttempt.user_id == user_id, LevelExamAttempt.level == level)
            .order_by(LevelExamAttempt.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def has_passed(self, user_id: uuid.UUID, level: CEFRLevel) -> bool:
        result = await self._session.execute(
            select(LevelExamAttempt.id)
            .where(
                LevelExamAttempt.user_id == user_id,
                LevelExamAttempt.level == level,
                LevelExamAttempt.passed.is_(True),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
