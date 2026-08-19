from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import LevelLockedError, NotFoundError
from app.models.learning_profile import CEFRLevel
from app.models.lesson import Lesson
from app.models.module import Module
from app.models.user import User
from app.schemas.course import (
    LessonDetailResponse,
    LessonSummaryResponse,
    LevelResponse,
    ModuleResponse,
)
from app.services.course_service import CourseService

router = APIRouter(tags=["course"])


@router.get("/levels", response_model=list[LevelResponse])
async def list_levels(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[LevelResponse]:
    levels = await CourseService(session).list_levels(current_user.id)
    return [
        LevelResponse(id=level.id, code=level.code, order_index=level.order_index, unlocked=unlocked)
        for level, unlocked in levels
    ]


@router.get("/levels/{level_code}/modules", response_model=list[ModuleResponse])
async def list_modules(
    level_code: CEFRLevel,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Module]:
    try:
        return await CourseService(session).list_modules(current_user.id, level_code)
    except LevelLockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/modules/{module_slug}/lessons", response_model=list[LessonSummaryResponse])
async def list_lessons(
    module_slug: str,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[Lesson]:
    return await CourseService(session).list_lessons(module_slug)


@router.get("/lessons/{lesson_slug}", response_model=LessonDetailResponse)
async def get_lesson(
    lesson_slug: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Lesson:
    try:
        return await CourseService(session).get_lesson(current_user.id, lesson_slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LevelLockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
