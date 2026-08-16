import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_mistake import MistakeStatus, UserMistake


class MistakeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_and_topic(
        self, user_id: uuid.UUID, grammar_topic_id: uuid.UUID
    ) -> UserMistake | None:
        result = await self._session.execute(
            select(UserMistake).where(
                UserMistake.user_id == user_id, UserMistake.grammar_topic_id == grammar_topic_id
            )
        )
        return result.scalar_one_or_none()

    def add(self, mistake: UserMistake) -> None:
        self._session.add(mistake)

    async def list_by_user(
        self, user_id: uuid.UUID, status: MistakeStatus | None = None
    ) -> Sequence[UserMistake]:
        query = (
            select(UserMistake)
            .where(UserMistake.user_id == user_id)
            .options(selectinload(UserMistake.grammar_topic))
            .order_by(UserMistake.last_attempt_at.desc())
        )
        if status is not None:
            query = query.where(UserMistake.status == status)
        result = await self._session.execute(query)
        return result.scalars().all()
