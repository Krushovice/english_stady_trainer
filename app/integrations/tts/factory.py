from functools import lru_cache

from app.core.config import Settings, get_settings
from app.integrations.tts.kokoro_provider import KokoroTTSProvider
from app.integrations.tts.provider import TTSProvider


def build_tts_provider(settings: Settings) -> TTSProvider:
    if settings.tts_provider == "kokoro":
        return KokoroTTSProvider(
            base_url=settings.tts_base_url,
            api_key=settings.tts_api_key,
            voice=settings.tts_voice,
            timeout_seconds=settings.tts_timeout_seconds,
        )
    raise ValueError(f"Unknown TTS_PROVIDER: {settings.tts_provider!r}")


@lru_cache
def get_tts_provider() -> TTSProvider:
    """Accessor for `scripts/generate_audio.py`; override with a
    `MockTTSProvider` in tests. Not a FastAPI dependency — no live route
    calls TTS, unlike STT/AI."""
    return build_tts_provider(get_settings())
