from typing import Protocol


class TTSProvider(Protocol):
    """Text-to-speech abstraction the audio-generation batch script is built
    on, so the underlying vendor/model can change without touching that
    script — mirrors `app.integrations.stt.provider.STTProvider`.
    """

    async def synthesize(self, text: str) -> bytes: ...
