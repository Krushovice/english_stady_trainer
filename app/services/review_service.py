import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.review_item import ReviewItem, ReviewItemType
from app.repositories.review_repository import ReviewRepository
from app.services.spaced_repetition import DEFAULT_EASE_FACTOR, ReviewState, schedule_next_review

_ITEM_TYPE_FIELD = {
    ReviewItemType.VOCABULARY: "vocabulary_id",
    ReviewItemType.GRAMMAR_TOPIC: "grammar_topic_id",
    ReviewItemType.EXERCISE: "exercise_id",
}


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ReviewRepository(session)

    async def record_outcome(
        self, user_id: uuid.UUID, item_type: ReviewItemType, target_id: uuid.UUID, is_correct: bool
    ) -> ReviewItem:
        """Update (or create) the review schedule for one item.

        Only adds/flushes — called from within `ExerciseService.submit_attempt`'s
        transaction, which owns the commit.
        """
        review_item = await self._repo.get_by_user_and_item(user_id, item_type, target_id)
        if review_item is None:
            review_item = ReviewItem(
                user_id=user_id,
                item_type=item_type,
                interval_days=0,
                ease_factor=DEFAULT_EASE_FACTOR,
                review_count=0,
                **{_ITEM_TYPE_FIELD[item_type]: target_id},
            )
            self._repo.add(review_item)

        self._apply_schedule(review_item, is_correct)
        await self._session.flush()
        return review_item

    async def list_due(self, user_id: uuid.UUID, limit: int = 20) -> list[ReviewItem]:
        return list(await self._repo.list_due(user_id, datetime.now(UTC), limit))

    async def complete_review(
        self, user_id: uuid.UUID, review_item_id: uuid.UUID, is_correct: bool
    ) -> ReviewItem:
        review_item = await self._repo.get_by_id(user_id, review_item_id)
        if review_item is None:
            raise NotFoundError(f"Review item '{review_item_id}' not found")

        self._apply_schedule(review_item, is_correct)
        await self._session.commit()
        return review_item

    def _apply_schedule(self, review_item: ReviewItem, is_correct: bool) -> None:
        now = datetime.now(UTC)
        current_state = ReviewState(
            interval_days=review_item.interval_days,
            ease_factor=review_item.ease_factor,
            review_count=review_item.review_count,
        )
        new_state, due_at = schedule_next_review(current_state, is_correct, now)

        review_item.interval_days = new_state.interval_days
        review_item.ease_factor = new_state.ease_factor
        review_item.review_count = new_state.review_count
        review_item.due_at = due_at
        review_item.last_reviewed_at = now
