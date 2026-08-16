from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import NotFoundError
from app.models.exercise import Exercise
from app.models.user import User
from app.schemas.exercise import ExercisePublicResponse
from app.schemas.placement import (
    PlacementResultResponse,
    PlacementSubmitRequest,
    RecommendedModuleResponse,
    SkillLevelResult,
)
from app.services.placement_service import PlacementResult, PlacementService

router = APIRouter(prefix="/placement-test", tags=["placement"])


def _to_response(result: PlacementResult) -> PlacementResultResponse:
    return PlacementResultResponse(
        overall_level=result.overall_level,
        skills=[
            SkillLevelResult(
                skill=skill_result.skill,
                level=skill_result.level,
                correct=skill_result.correct,
                total=skill_result.total,
            )
            for skill_result in result.skills
        ],
        recommended_modules=[
            RecommendedModuleResponse(
                id=module.id, slug=module.slug, title=module.title, level_code=module.level.code
            )
            for module in result.recommended_modules
        ],
        placement_completed_at=result.placement_completed_at,
    )


@router.get("/items", response_model=list[ExercisePublicResponse])
async def get_placement_items(
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> list[Exercise]:
    return await PlacementService(session).get_test_items()


@router.post("/submit", response_model=PlacementResultResponse)
async def submit_placement_test(
    payload: PlacementSubmitRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PlacementResultResponse:
    service = PlacementService(session)
    try:
        result = await service.submit(
            user_id=current_user.id,
            answers=[(answer.exercise_id, answer.submitted_answer) for answer in payload.answers],
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(result)


@router.get("/result", response_model=PlacementResultResponse)
async def get_placement_result(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PlacementResultResponse:
    service = PlacementService(session)
    try:
        result = await service.get_result(current_user.id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(result)
