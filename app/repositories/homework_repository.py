import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.homework import Homework, HomeworkAttempt


class HomeworkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, homework: Homework) -> None:
        self._session.add(homework)

    async def get_by_id(self, homework_id: uuid.UUID) -> Homework | None:
        result = await self._session.execute(
            select(Homework)
            .where(Homework.id == homework_id)
            .options(
                selectinload(Homework.lesson),
                selectinload(Homework.attempts),
            )
        )
        return result.scalar_one_or_none()

    def add_attempt(self, attempt: HomeworkAttempt) -> None:
        self._session.add(attempt)

    async def list_attempts(self, homework_id: uuid.UUID) -> Sequence[HomeworkAttempt]:
        result = await self._session.execute(
            select(HomeworkAttempt)
            .where(HomeworkAttempt.homework_id == homework_id)
            .order_by(HomeworkAttempt.submitted_at)
        )
        return result.scalars().all()
