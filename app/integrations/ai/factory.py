from functools import lru_cache

from app.core.config import Settings, get_settings
from app.integrations.ai.lmstudio_provider import LMStudioProvider
from app.integrations.ai.provider import AIProvider


def build_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "lmstudio":
        return LMStudioProvider(
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            timeout_seconds=settings.ai_timeout_seconds,
        )
    raise ValueError(f"Unknown AI_PROVIDER: {settings.ai_provider!r}")


@lru_cache
def get_ai_provider() -> AIProvider:
    """FastAPI-dependency-shaped accessor; override with a `MockAIProvider` in tests."""
    return build_ai_provider(get_settings())
