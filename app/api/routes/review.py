import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import NotFoundError
from app.models.review_item import ReviewItem
from app.models.user import User
from app.schemas.review import CompleteReviewRequest, ReviewItemResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/due", response_model=list[ReviewItemResponse])
async def list_due_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[ReviewItem]:
    return await ReviewService(session).list_due(current_user.id, limit)


@router.post("/{review_item_id}/complete", response_model=ReviewItemResponse)
async def complete_review(
    review_item_id: uuid.UUID,
    payload: CompleteReviewRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ReviewItem:
    try:
        return await ReviewService(session).complete_review(
            current_user.id, review_item_id, payload.is_correct
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
