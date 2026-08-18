import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
from app.core.exceptions import (
    AIProviderUnavailableError,
    AIResponseParsingError,
    ConversationEndedError,
    NotFoundError,
)
from app.integrations.ai.factory import get_ai_provider
from app.integrations.ai.provider import AIProvider
from app.models.conversation import ConversationMessage, ConversationSession
from app.models.user import User
from app.schemas.conversation import (
    ConversationAnalysisResponse,
    ConversationMessageResponse,
    ConversationSessionResponse,
    SendConversationMessageRequest,
    StartConversationRequest,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversation", tags=["conversation"])


def _message_to_response(message: ConversationMessage) -> ConversationMessageResponse:
    return ConversationMessageResponse(
        id=message.id, role=message.role, content=message.content, created_at=message.created_at
    )


def _session_to_response(conversation: ConversationSession) -> ConversationSessionResponse:
    return ConversationSessionResponse(
        id=conversation.id,
        topic=conversation.topic,
        started_at=conversation.started_at,
        ended_at=conversation.ended_at,
        messages=[_message_to_response(m) for m in conversation.messages],
        analysis=(
            ConversationAnalysisResponse(**conversation.analysis)
            if conversation.analysis is not None
            else None
        ),
    )


@router.post("/sessions", response_model=ConversationSessionResponse)
async def start_conversation(
    payload: StartConversationRequest,
    session: AsyncSession = Depends(get_db_session),
    provider: AIProvider = Depends(get_ai_provider),
    current_user: User = Depends(get_current_user),
) -> ConversationSessionResponse:
    try:
        conversation = await ConversationService(session).start(
            current_user.id, payload.topic, provider, max_tokens=get_settings().ai_max_tokens
        )
    except AIProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI conversation partner is temporarily unavailable. Please try again shortly.",
        ) from exc

    return _session_to_response(conversation)


@router.post("/sessions/{session_id}/messages", response_model=ConversationMessageResponse)
async def send_conversation_message(
    session_id: uuid.UUID,
    payload: SendConversationMessageRequest,
    session: AsyncSession = Depends(get_db_session),
    provider: AIProvider = Depends(get_ai_provider),
    current_user: User = Depends(get_current_user),
) -> ConversationMessageResponse:
    try:
        reply = await ConversationService(session).send_message(
            current_user.id,
            session_id,
            payload.text,
            provider,
            max_tokens=get_settings().ai_max_tokens,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConversationEndedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI conversation partner is temporarily unavailable. Please try again shortly.",
        ) from exc

    return _message_to_response(reply)


@router.post("/sessions/{session_id}/end", response_model=ConversationSessionResponse)
async def end_conversation(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    provider: AIProvider = Depends(get_ai_provider),
    current_user: User = Depends(get_current_user),
) -> ConversationSessionResponse:
    try:
        conversation = await ConversationService(session).end(
            current_user.id, session_id, provider, max_tokens=get_settings().ai_max_tokens
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI conversation partner is temporarily unavailable. Please try again shortly.",
        ) from exc
    except AIResponseParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Couldn't generate the session analysis this time. Please try again.",
        ) from exc

    return _session_to_response(conversation)


@router.get("/sessions/{session_id}", response_model=ConversationSessionResponse)
async def get_conversation(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ConversationSessionResponse:
    try:
        conversation = await ConversationService(session).get(current_user.id, session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _session_to_response(conversation)
