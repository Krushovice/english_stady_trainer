from functools import lru_cache

from app.core.config import Settings, get_settings
from app.integrations.stt.provider import STTProvider
from app.integrations.stt.speaches_provider import SpeachesProvider


def build_stt_provider(settings: Settings) -> STTProvider:
    if settings.stt_provider == "speaches":
        return SpeachesProvider(
            base_url=settings.stt_base_url,
            api_key=settings.stt_api_key,
            model=settings.stt_model,
            timeout_seconds=settings.stt_timeout_seconds,
        )
    raise ValueError(f"Unknown STT_PROVIDER: {settings.stt_provider!r}")


@lru_cache
def get_stt_provider() -> STTProvider:
    """FastAPI-dependency-shaped accessor; override with a `MockSTTProvider` in tests."""
    return build_stt_provider(get_settings())
