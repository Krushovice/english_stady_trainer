import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_exam_attempt import CourseExamAttempt


class CourseExamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, attempt: CourseExamAttempt) -> CourseExamAttempt:
        self._session.add(attempt)
        await self._session.flush()
        return attempt

    async def get_by_id(self, attempt_id: uuid.UUID) -> CourseExamAttempt | None:
        return await self._session.get(CourseExamAttempt, attempt_id)

    async def list_recent(self, user_id: uuid.UUID, *, limit: int) -> Sequence[CourseExamAttempt]:
        result = await self._session.execute(
            select(CourseExamAttempt)
            .where(CourseExamAttempt.user_id == user_id)
            .order_by(CourseExamAttempt.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def has_passed(self, user_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(CourseExamAttempt.id)
            .where(CourseExamAttempt.user_id == user_id, CourseExamAttempt.passed.is_(True))
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_passed_attempt(self, user_id: uuid.UUID) -> CourseExamAttempt | None:
        """The user's passed attempt, if any — at most one can ever exist,
        since passing raises ExamAlreadyPassedError on further attempts."""
        result = await self._session.execute(
            select(CourseExamAttempt).where(
                CourseExamAttempt.user_id == user_id, CourseExamAttempt.passed.is_(True)
            )
        )
        return result.scalar_one_or_none()
