from app.integrations.ai.provider import AIMessage


class MockAIProvider:
    """Canned-response stand-in for tests — never makes a network call.

    CLAUDE.md requires AI-dependent functionality to be testable without
    depending on real external AI responses; this is that seam.
    """

    def __init__(self, response: str = "Mock AI response.") -> None:
        self.response = response
        self.received_calls: list[list[AIMessage]] = []

    async def complete(self, messages: list[AIMessage], *, max_tokens: int) -> str:
        self.received_calls.append(messages)
        return self.response
