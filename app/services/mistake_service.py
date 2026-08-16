import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_mistake import MistakeStatus, UserMistake
from app.repositories.mistake_repository import MistakeRepository
from app.services.mistake_classification import MistakeState, classify_attempt


class MistakeService:
    """Classifies grammar-topic mistakes from exercise attempts.

    `record_attempt` only adds/flushes — it's called from within
    `ExerciseService.submit_attempt`'s transaction, which owns the commit.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = MistakeRepository(session)

    async def record_attempt(
        self, user_id: uuid.UUID, grammar_topic_id: uuid.UUID, is_correct: bool
    ) -> UserMistake | None:
        mistake = await self._repo.get_by_user_and_topic(user_id, grammar_topic_id)
        current_state = (
            MistakeState(
                status=mistake.status,
                total_attempts=mistake.total_attempts,
                incorrect_attempts=mistake.incorrect_attempts,
                consecutive_correct=mistake.consecutive_correct,
            )
            if mistake is not None
            else None
        )

        new_state = classify_attempt(current_state, is_correct)
        if new_state is None:
            return None  # no mistake to record: never wrong before, and correct now

        now = datetime.now(UTC)
        if mistake is None:
            mistake = UserMistake(user_id=user_id, grammar_topic_id=grammar_topic_id)
            self._repo.add(mistake)

        mistake.status = new_state.status
        mistake.total_attempts = new_state.total_attempts
        mistake.incorrect_attempts = new_state.incorrect_attempts
        mistake.consecutive_correct = new_state.consecutive_correct
        mistake.last_attempt_at = now
        await self._session.flush()
        return mistake

    async def list_mistakes(
        self, user_id: uuid.UUID, status: MistakeStatus | None = None
    ) -> list[UserMistake]:
        return list(await self._repo.list_by_user(user_id, status))
