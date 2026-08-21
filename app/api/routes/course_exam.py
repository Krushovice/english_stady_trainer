import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import (
    ExamAlreadyPassedError,
    ExamAttemptAlreadySubmittedError,
    ExamAttemptNotFoundError,
    ExamOnCooldownError,
    LevelLockedError,
    NotFoundError,
)
from app.models.user import User
from app.schemas.course_exam import (
    CourseExamAttemptResponse,
    CourseExamResultResponse,
    CourseExamStatusResponse,
    CourseExamSubmitRequest,
)
from app.services.course_exam_service import CourseExamService

router = APIRouter(prefix="/course-exam", tags=["course-exam"])


@router.get("/status", response_model=CourseExamStatusResponse)
async def get_course_exam_status(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CourseExamStatusResponse:
    status_ = await CourseExamService(session).get_status(current_user.id)
    return CourseExamStatusResponse(
        exam_available=status_.exam_available,
        passed=status_.passed,
        attempts_used_in_window=status_.attempts_used_in_window,
        attempts_per_window=status_.attempts_per_window,
        cooldown_until=status_.cooldown_until,
        in_progress_attempt_id=status_.in_progress.id if status_.in_progress else None,
        in_progress_expires_at=status_.in_progress.expires_at if status_.in_progress else None,
        certificate_available=status_.certificate_available,
        earned_at=status_.earned_at,
    )


@router.post("/attempts", response_model=CourseExamAttemptResponse)
async def start_course_exam_attempt(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CourseExamAttemptResponse:
    try:
        attempt, exercises = await CourseExamService(session).start_attempt(current_user.id)
    except LevelLockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ExamAlreadyPassedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ExamOnCooldownError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CourseExamAttemptResponse(
        attempt_id=attempt.id, expires_at=attempt.expires_at, exercises=exercises
    )


@router.post("/attempts/{attempt_id}/submit", response_model=CourseExamResultResponse)
async def submit_course_exam_attempt(
    attempt_id: uuid.UUID,
    payload: CourseExamSubmitRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CourseExamResultResponse:
    try:
        attempt = await CourseExamService(session).submit_attempt(
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
    return CourseExamResultResponse(
        attempt_id=attempt.id,
        score=float(attempt.score) if attempt.score is not None else 0.0,
        passed=bool(attempt.passed),
        correct_count=correct_count,
        total_count=total_count,
    )
