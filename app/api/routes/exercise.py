import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import NotFoundError
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.user import User
from app.schemas.exercise import (
    AttemptHistoryResponse,
    AttemptResultResponse,
    ExercisePublicResponse,
    SkillProgressResponse,
    SubmitAttemptRequest,
)
from app.services.exercise_service import ExerciseService
from app.services.scoring import InvalidSubmissionError

router = APIRouter(tags=["exercises"])


@router.get("/lessons/{lesson_slug}/exercises", response_model=list[ExercisePublicResponse])
async def list_lesson_exercises(
    lesson_slug: str,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list:
    return await ExerciseService(session).list_lesson_exercises(lesson_slug)


@router.post("/exercises/{exercise_id}/attempts", response_model=AttemptResultResponse)
async def submit_attempt(
    exercise_id: uuid.UUID,
    payload: SubmitAttemptRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExerciseAttempt:
    service = ExerciseService(session)
    try:
        attempt = await service.submit_attempt(
            user_id=current_user.id,
            exercise_id=exercise_id,
            submitted_answer=payload.submitted_answer,
            source=payload.source,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidSubmissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return AttemptResultResponse(
        id=attempt.id,
        is_correct=attempt.is_correct,
        score=attempt.score,
        explanation=attempt.exercise.explanation,
        answer_key=attempt.exercise.answer_key,
        attempted_at=attempt.attempted_at,
    )


@router.get("/exercises/{exercise_id}/attempts", response_model=list[AttemptHistoryResponse])
async def list_attempts(
    exercise_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list:
    return await ExerciseService(session).list_attempts(current_user.id, exercise_id)


@router.get("/practice/daily-quiz", response_model=list[ExercisePublicResponse])
async def get_daily_quiz(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Exercise]:
    return await ExerciseService(session).get_daily_quiz(current_user.id, today=date.today())


@router.get("/progress", response_model=list[SkillProgressResponse])
async def get_progress(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[SkillProgressResponse]:
    rows = await ExerciseService(session).get_progress(current_user.id)
    return [
        SkillProgressResponse(
            skill=row.skill,
            attempts_count=row.attempts_count,
            correct_count=row.correct_count,
            accuracy=(row.correct_count / row.attempts_count) if row.attempts_count else 0,
        )
        for row in rows
    ]
