from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.models.user_mistake import MistakeStatus, UserMistake
from app.schemas.mistake import UserMistakeResponse
from app.services.mistake_service import MistakeService

router = APIRouter(tags=["mistakes"])


@router.get("/mistakes", response_model=list[UserMistakeResponse])
async def list_mistakes(
    status_filter: MistakeStatus | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[UserMistake]:
    return await MistakeService(session).list_mistakes(current_user.id, status_filter)
