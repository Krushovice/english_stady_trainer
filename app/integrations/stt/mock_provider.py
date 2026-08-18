class MockSTTProvider:
    """Canned-response stand-in for tests — never makes a network call.

    Same purpose as `app.integrations.ai.mock_provider.MockAIProvider`: no
    AI/STT-dependent test may depend on a real external model.
    """

    def __init__(self, transcript: str = "This is a mock transcript.") -> None:
        self.transcript = transcript
        self.received_calls: list[tuple[bytes, str, str]] = []

    async def transcribe(self, audio: bytes, filename: str, *, language: str) -> str:
        self.received_calls.append((audio, filename, language))
        return self.transcript
