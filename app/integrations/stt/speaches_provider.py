from openai import APIConnectionError, APITimeoutError, AsyncOpenAI

from app.core.exceptions import STTProviderUnavailableError


class SpeachesProvider:
    """Talks to a Speaches server (github.com/speaches-ai/speaches) over its
    OpenAI-compatible `/v1/audio/transcriptions` endpoint.

    Speaches wraps faster-whisper and runs as an ordinary Docker container
    (unlike LM Studio, which is a native host GUI app) — see docs/decisions.md.
    """

    def __init__(self, base_url: str, api_key: str, model: str, timeout_seconds: float) -> None:
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key, timeout=timeout_seconds)
        self._model = model

    async def transcribe(self, audio: bytes, filename: str, *, language: str) -> str:
        try:
            response = await self._client.audio.transcriptions.create(
                file=(filename, audio),
                model=self._model,
                language=language,
            )
        except (APIConnectionError, APITimeoutError) as exc:
            raise STTProviderUnavailableError(
                f"STT provider at {self._client.base_url} is unreachable"
            ) from exc

        return response.text
