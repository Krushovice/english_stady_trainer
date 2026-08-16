import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review_item import ReviewItem, ReviewItemType

_ITEM_TYPE_COLUMN = {
    ReviewItemType.VOCABULARY: ReviewItem.vocabulary_id,
    ReviewItemType.GRAMMAR_TOPIC: ReviewItem.grammar_topic_id,
    ReviewItemType.EXERCISE: ReviewItem.exercise_id,
}

# Every read that might be serialized as ReviewItemResponse needs these
# eager-loaded — the response reads .vocabulary/.grammar_topic/.exercise,
# and a lazy load outside an async context raises MissingGreenlet.
_TARGET_LOAD_OPTIONS = (
    selectinload(ReviewItem.vocabulary),
    selectinload(ReviewItem.grammar_topic),
    selectinload(ReviewItem.exercise),
)


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_and_item(
        self, user_id: uuid.UUID, item_type: ReviewItemType, target_id: uuid.UUID
    ) -> ReviewItem | None:
        column = _ITEM_TYPE_COLUMN[item_type]
        result = await self._session.execute(
            select(ReviewItem).where(ReviewItem.user_id == user_id, column == target_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID, review_item_id: uuid.UUID) -> ReviewItem | None:
        result = await self._session.execute(
            select(ReviewItem)
            .where(ReviewItem.user_id == user_id, ReviewItem.id == review_item_id)
            .options(*_TARGET_LOAD_OPTIONS)
        )
        return result.scalar_one_or_none()

    def add(self, review_item: ReviewItem) -> None:
        self._session.add(review_item)

    async def list_due(self, user_id: uuid.UUID, now: datetime, limit: int) -> Sequence[ReviewItem]:
        result = await self._session.execute(
            select(ReviewItem)
            .where(ReviewItem.user_id == user_id, ReviewItem.due_at <= now)
            .options(*_TARGET_LOAD_OPTIONS)
            .order_by(ReviewItem.due_at)
            .limit(limit)
        )
        return result.scalars().all()
