from typing import Protocol


class TTSProvider(Protocol):
    """Text-to-speech abstraction the audio-generation batch script is built
    on, so the underlying vendor/model can change without touching that
    script — mirrors `app.integrations.stt.provider.STTProvider`.

    `voice` overrides the provider's configured default for this one call —
    used by `scripts/generate_audio.py` to give each speaker in a dialogue
    a distinct voice instead of narrating the whole thing in one.
    """

    async def synthesize(self, text: str, voice: str | None = None) -> bytes: ...
