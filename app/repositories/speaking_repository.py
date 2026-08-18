import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.speaking import SpeakingAttempt


class SpeakingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, attempt: SpeakingAttempt) -> None:
        self._session.add(attempt)

    async def get_by_id(self, attempt_id: uuid.UUID) -> SpeakingAttempt | None:
        result = await self._session.execute(
            select(SpeakingAttempt)
            .where(SpeakingAttempt.id == attempt_id)
            .options(selectinload(SpeakingAttempt.lesson))
        )
        return result.scalar_one_or_none()
