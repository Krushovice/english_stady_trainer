import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
from app.core.exceptions import AIProviderUnavailableError, AIResponseParsingError, NotFoundError
from app.integrations.ai.factory import get_ai_provider
from app.integrations.ai.provider import AIProvider
from app.models.homework import Homework, HomeworkAttempt
from app.models.user import User
from app.schemas.ai import WritingFeedbackResponse
from app.schemas.homework import (
    HomeworkAttemptResponse,
    HomeworkResponse,
    HomeworkTaskResponse,
    SubmitHomeworkTaskRequest,
)
from app.services.homework_service import HomeworkService

router = APIRouter(prefix="/homework", tags=["homework"])


def _attempt_to_response(attempt: HomeworkAttempt) -> HomeworkAttemptResponse:
    return HomeworkAttemptResponse(
        id=attempt.id,
        task_id=attempt.task_id,
        submitted_text=attempt.submitted_text,
        feedback=WritingFeedbackResponse(**attempt.feedback),
        submitted_at=attempt.submitted_at,
    )


def _to_response(homework: Homework) -> HomeworkResponse:
    return HomeworkResponse(
        id=homework.id,
        lesson_title=homework.lesson.title,
        tasks=[HomeworkTaskResponse(**task) for task in homework.tasks],
        attempts=[_attempt_to_response(attempt) for attempt in homework.attempts],
        generated_at=homework.generated_at,
    )


@router.post("/generate", response_model=HomeworkResponse)
async def generate_homework(
    session: AsyncSession = Depends(get_db_session),
    provider: AIProvider = Depends(get_ai_provider),
    current_user: User = Depends(get_current_user),
) -> HomeworkResponse:
    try:
        homework = await HomeworkService(session).generate(
            current_user.id, provider, max_tokens=get_settings().ai_max_tokens
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AIProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI homework generation is temporarily unavailable. Please try again shortly.",
        ) from exc
    except AIResponseParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Couldn't generate homework this time. Please try again.",
        ) from exc

    return _to_response(homework)


@router.get("/{homework_id}", response_model=HomeworkResponse)
async def get_homework(
    homework_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> HomeworkResponse:
    try:
        homework = await HomeworkService(session).get(current_user.id, homework_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(homework)


@router.post("/{homework_id}/tasks/{task_id}/submit", response_model=HomeworkAttemptResponse)
async def submit_homework_task(
    homework_id: uuid.UUID,
    task_id: str,
    payload: SubmitHomeworkTaskRequest,
    session: AsyncSession = Depends(get_db_session),
    provider: AIProvider = Depends(get_ai_provider),
    current_user: User = Depends(get_current_user),
) -> HomeworkAttemptResponse:
    try:
        attempt = await HomeworkService(session).submit_task(
            current_user.id,
            homework_id,
            task_id,
            payload.text,
            provider,
            max_tokens=get_settings().ai_max_tokens,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
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

    return _attempt_to_response(attempt)
