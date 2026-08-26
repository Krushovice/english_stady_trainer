import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
from app.core.exceptions import (
    AIProviderUnavailableError,
    AIResponseParsingError,
    EmptyTranscriptError,
    NotFoundError,
    SpeakingAttemptAlreadySubmittedError,
    STTProviderUnavailableError,
)
from app.integrations.ai.factory import get_ai_provider
from app.integrations.ai.provider import AIProvider
from app.integrations.stt.factory import get_stt_provider
from app.integrations.stt.provider import STTProvider
from app.models.speaking import SpeakingAttempt
from app.models.user import User
from app.schemas.ai import WritingFeedbackResponse
from app.schemas.speaking import SpeakingAttemptResponse
from app.services.speaking_service import SpeakingService

router = APIRouter(prefix="/speaking", tags=["speaking"])

# A task asks for ~30-60s of speech; this is a generous ceiling to guard
# against an accidental or abusive oversized upload tying up the STT
# provider, not a precise duration limit.
_MAX_AUDIO_BYTES = 15 * 1024 * 1024


def _to_response(attempt: SpeakingAttempt) -> SpeakingAttemptResponse:
    return SpeakingAttemptResponse(
        id=attempt.id,
        lesson_title=attempt.lesson.title,
        prompt=attempt.prompt,
        transcript=attempt.transcript,
        feedback=WritingFeedbackResponse(**attempt.feedback) if attempt.feedback else None,
        generated_at=attempt.generated_at,
        submitted_at=attempt.submitted_at,
    )


@router.post("/prompts", response_model=SpeakingAttemptResponse)
async def generate_speaking_prompt(
    session: AsyncSession = Depends(get_db_session),
    provider: AIProvider = Depends(get_ai_provider),
    current_user: User = Depends(get_current_user),
) -> SpeakingAttemptResponse:
    try:
        attempt = await SpeakingService(session).generate_prompt(
            current_user.id, provider, max_tokens=get_settings().ai_max_tokens
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI speaking-prompt generation is temporarily unavailable. "
            "Please try again shortly.",
        ) from exc
    except AIResponseParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Couldn't generate a speaking prompt this time. Please try again.",
        ) from exc

    return _to_response(attempt)


@router.post("/lessons/{lesson_slug}/attempts", response_model=SpeakingAttemptResponse)
async def start_lesson_speaking_attempt(
    lesson_slug: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> SpeakingAttemptResponse:
    try:
        attempt = await SpeakingService(session).start_lesson_attempt(current_user.id, lesson_slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(attempt)


@router.get("/attempts/{attempt_id}", response_model=SpeakingAttemptResponse)
async def get_speaking_attempt(
    attempt_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> SpeakingAttemptResponse:
    try:
        attempt = await SpeakingService(session).get(current_user.id, attempt_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(attempt)


@router.post("/attempts/{attempt_id}/submit", response_model=SpeakingAttemptResponse)
async def submit_speaking_attempt(
    attempt_id: uuid.UUID,
    audio: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    ai_provider: AIProvider = Depends(get_ai_provider),
    stt_provider: STTProvider = Depends(get_stt_provider),
    current_user: User = Depends(get_current_user),
) -> SpeakingAttemptResponse:
    audio_bytes = await audio.read()
    if len(audio_bytes) > _MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file is too large.",
        )

    try:
        attempt = await SpeakingService(session).submit_attempt(
            current_user.id,
            attempt_id,
            audio_bytes,
            audio.filename or "recording.wav",
            stt_provider,
            ai_provider,
            max_tokens=get_settings().ai_max_tokens,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SpeakingAttemptAlreadySubmittedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except EmptyTranscriptError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    except STTProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech-to-text is temporarily unavailable. Please try again shortly.",
        ) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI feedback is temporarily unavailable. Please try again shortly.",
        ) from exc
    except AIResponseParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Couldn't generate feedback this time. Please try again.",
        ) from exc

    return _to_response(attempt)
