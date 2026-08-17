from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AIProviderUnavailableError, AIResponseParsingError
from app.integrations.ai.factory import get_ai_provider
from app.integrations.ai.provider import AIProvider
from app.models.user import User
from app.schemas.ai import WritingFeedbackRequest, WritingFeedbackResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/writing", tags=["ai"])


@router.post("/feedback", response_model=WritingFeedbackResponse)
async def get_writing_feedback(
    payload: WritingFeedbackRequest,
    provider: AIProvider = Depends(get_ai_provider),
    current_user: User = Depends(get_current_user),
) -> WritingFeedbackResponse:
    try:
        feedback = await AIService(provider).generate_writing_feedback(
            payload.text, max_tokens=get_settings().ai_max_tokens
        )
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

    return WritingFeedbackResponse(
        good=feedback.good,
        grammar=feedback.grammar,
        vocabulary=feedback.vocabulary,
        natural_version=feedback.natural_version,
        try_again=feedback.try_again,
    )
