import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import ConversationMessage, ConversationSession


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, conversation: ConversationSession) -> None:
        self._session.add(conversation)

    def add_message(self, message: ConversationMessage) -> None:
        self._session.add(message)

    async def get_by_id(self, session_id: uuid.UUID) -> ConversationSession | None:
        result = await self._session.execute(
            select(ConversationSession)
            .where(ConversationSession.id == session_id)
            .options(selectinload(ConversationSession.messages))
        )
        return result.scalar_one_or_none()
