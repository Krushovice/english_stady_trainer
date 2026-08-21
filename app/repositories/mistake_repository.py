import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
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

    async def count_by_status(self, user_id: uuid.UUID) -> dict[MistakeStatus, int]:
        """Number of grammar topics currently in each mistake status —
        one row per (user, grammar_topic), so this is a topic count, not an
        attempt count. Missing statuses default to 0 so callers never need
        a fallback lookup."""
        counts = {status: 0 for status in MistakeStatus}
        result = await self._session.execute(
            select(UserMistake.status, func.count())
            .where(UserMistake.user_id == user_id)
            .group_by(UserMistake.status)
        )
        for status, count in result.all():
            counts[status] = count
        return counts
