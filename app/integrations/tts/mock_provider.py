class MockTTSProvider:
    """Canned-response stand-in for tests — never makes a network call.

    Same purpose as `app.integrations.stt.mock_provider.MockSTTProvider`: no
    TTS-dependent test may depend on a real external model.
    """

    def __init__(self, audio: bytes = b"mock-audio-bytes") -> None:
        self.audio = audio
        self.received_calls: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.received_calls.append(text)
        return self.audio
