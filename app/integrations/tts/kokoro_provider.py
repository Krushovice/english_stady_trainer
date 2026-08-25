from openai import APIConnectionError, APITimeoutError, AsyncOpenAI

from app.core.exceptions import TTSProviderUnavailableError


class KokoroTTSProvider:
    """Talks to a Kokoro-FastAPI server (github.com/remsky/Kokoro-FastAPI)
    over its OpenAI-compatible `/v1/audio/speech` endpoint.

    Kokoro runs as an ordinary Docker container (unlike LM Studio, which is
    a native host GUI app) — same reasoning as `SpeachesProvider`. Chosen
    over the browser's Web Speech API after the user tested that live and
    rejected it for quality (see docs/decisions.md).
    """

    def __init__(self, base_url: str, api_key: str, voice: str, timeout_seconds: float) -> None:
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key, timeout=timeout_seconds)
        self._voice = voice

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        try:
            response = await self._client.audio.speech.create(
                model="kokoro",
                input=text,
                voice=voice or self._voice,
                response_format="mp3",
            )
        except (APIConnectionError, APITimeoutError) as exc:
            raise TTSProviderUnavailableError(
                f"TTS provider at {self._client.base_url} is unreachable"
            ) from exc

        return await response.aread()
