import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import (
    ExamAlreadyPassedError,
    ExamAttemptAlreadySubmittedError,
    ExamAttemptNotFoundError,
    ExamOnCooldownError,
    NotFoundError,
)
from app.models.learning_profile import CEFRLevel
from app.models.user import User
from app.schemas.level_exam import (
    ExamAttemptResponse,
    ExamResultResponse,
    ExamStatusResponse,
    ExamSubmitRequest,
)
from app.services.level_exam_service import LevelExamService

router = APIRouter(prefix="/levels/{level_code}/exam", tags=["level-exam"])


@router.get("/status", response_model=ExamStatusResponse)
async def get_exam_status(
    level_code: CEFRLevel,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExamStatusResponse:
    status_ = await LevelExamService(session).get_status(current_user.id, level_code)
    return ExamStatusResponse(
        level=status_.level,
        exam_available=status_.exam_available,
        passed=status_.passed,
        attempts_used_in_window=status_.attempts_used_in_window,
        attempts_per_window=status_.attempts_per_window,
        cooldown_until=status_.cooldown_until,
        in_progress_attempt_id=status_.in_progress.id if status_.in_progress else None,
        in_progress_expires_at=status_.in_progress.expires_at if status_.in_progress else None,
    )


@router.post("/attempts", response_model=ExamAttemptResponse)
async def start_exam_attempt(
    level_code: CEFRLevel,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExamAttemptResponse:
    try:
        attempt, exercises = await LevelExamService(session).start_attempt(
            current_user.id, level_code
        )
    except ExamAlreadyPassedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ExamOnCooldownError as exc:
        # The structured retry_at lives on GET /status's `cooldown_until` —
        # the frontend checks that before ever offering a "start" button, so
        # this 429 is a defense-in-depth guard, not the primary signal path.
        # Keeping `detail` a plain string here matches apiRequest()'s
        # ApiError contract (frontend/src/api/client.ts), which only reads
        # `detail` when it's a string.
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ExamAttemptResponse(
        attempt_id=attempt.id, expires_at=attempt.expires_at, exercises=exercises
    )


@router.post("/attempts/{attempt_id}/submit", response_model=ExamResultResponse)
async def submit_exam_attempt(
    level_code: CEFRLevel,
    attempt_id: uuid.UUID,
    payload: ExamSubmitRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExamResultResponse:
    try:
        attempt = await LevelExamService(session).submit_attempt(
            user_id=current_user.id,
            attempt_id=attempt_id,
            answers={
                str(answer.exercise_id): answer.submitted_answer for answer in payload.answers
            },
        )
    except ExamAttemptNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExamAttemptAlreadySubmittedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    total_count = len(attempt.exercise_ids)
    correct_count = round(float(attempt.score) * total_count) if attempt.score is not None else 0
    return ExamResultResponse(
        attempt_id=attempt.id,
        score=float(attempt.score) if attempt.score is not None else 0.0,
        passed=bool(attempt.passed),
        correct_count=correct_count,
        total_count=total_count,
    )
