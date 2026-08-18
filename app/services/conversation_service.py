import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConversationEndedError, NotFoundError
from app.integrations.ai.provider import AIMessage, AIProvider
from app.models.conversation import ConversationMessage, ConversationRole, ConversationSession
from app.repositories.conversation_repository import ConversationRepository
from app.services.ai_service import AIService


class ConversationService:
    """Open-ended conversation practice: AI asks -> learner responds -> AI
    reacts naturally (no mid-conversation corrections) -> session ends ->
    analysis is generated. Matches CLAUDE.md's "AI Conversation" flow.

    Ownership checks (404, not 403, on a mismatched `user_id`) match the
    pattern already used for review items and homework.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)

    async def start(
        self, user_id: uuid.UUID, topic: str | None, ai_provider: AIProvider, *, max_tokens: int
    ) -> ConversationSession:
        opening_text = await AIService(ai_provider).start_conversation(topic, max_tokens=max_tokens)

        conversation = ConversationSession(user_id=user_id, topic=topic)
        conversation.messages.append(
            ConversationMessage(role=ConversationRole.ASSISTANT, content=opening_text, sequence=0)
        )
        self._conversations.add(conversation)
        await self._session.commit()
        return conversation

    async def send_message(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        text: str,
        ai_provider: AIProvider,
        *,
        max_tokens: int,
    ) -> ConversationMessage:
        conversation = await self._get_owned(user_id, session_id)
        if conversation.ended_at is not None:
            raise ConversationEndedError(f"Conversation '{session_id}' has already ended")

        history = [
            AIMessage(role=message.role.value, content=message.content)
            for message in conversation.messages
        ]
        history.append(AIMessage(role="user", content=text))
        reply_text = await AIService(ai_provider).continue_conversation(
            history, max_tokens=max_tokens
        )

        next_sequence = len(conversation.messages)
        self._conversations.add_message(
            ConversationMessage(
                session_id=conversation.id,
                role=ConversationRole.USER,
                content=text,
                sequence=next_sequence,
            )
        )
        reply = ConversationMessage(
            session_id=conversation.id,
            role=ConversationRole.ASSISTANT,
            content=reply_text,
            sequence=next_sequence + 1,
        )
        self._conversations.add_message(reply)
        await self._session.commit()
        return reply

    async def end(
        self, user_id: uuid.UUID, session_id: uuid.UUID, ai_provider: AIProvider, *, max_tokens: int
    ) -> ConversationSession:
        conversation = await self._get_owned(user_id, session_id)
        if conversation.ended_at is not None:
            return conversation  # idempotent: already analyzed, don't re-spend an AI call

        transcript = "\n".join(
            f"{'Learner' if message.role == ConversationRole.USER else 'Partner'}: "
            f"{message.content}"
            for message in conversation.messages
        )
        analysis = await AIService(ai_provider).generate_conversation_analysis(
            transcript, max_tokens=max_tokens
        )

        conversation.ended_at = datetime.now(UTC)
        conversation.analysis = {
            "recurring_mistakes": analysis.recurring_mistakes,
            "useful_vocabulary": analysis.useful_vocabulary,
            "natural_alternatives": analysis.natural_alternatives,
            "grammar_topics_to_review": analysis.grammar_topics_to_review,
            "recommended_practice": analysis.recommended_practice,
        }
        await self._session.commit()
        return conversation

    async def get(self, user_id: uuid.UUID, session_id: uuid.UUID) -> ConversationSession:
        return await self._get_owned(user_id, session_id)

    async def _get_owned(self, user_id: uuid.UUID, session_id: uuid.UUID) -> ConversationSession:
        conversation = await self._conversations.get_by_id(session_id)
        if conversation is None or conversation.user_id != user_id:
            raise NotFoundError(f"Conversation '{session_id}' not found")
        return conversation
