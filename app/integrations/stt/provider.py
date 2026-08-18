from typing import Protocol


class STTProvider(Protocol):
    """Speech-to-text abstraction the Speaking flow is built on, so the
    underlying transcription vendor/model can change without touching
    feature code — mirrors `app.integrations.ai.provider.AIProvider`.
    """

    async def transcribe(self, audio: bytes, filename: str, *, language: str) -> str: ...
