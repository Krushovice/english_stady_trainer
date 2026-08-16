import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_profile import LearningProfile


class LearningProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> LearningProfile | None:
        result = await self._session.execute(
            select(LearningProfile).where(LearningProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
