import uuid

from httpx import AsyncClient

from app.core.exceptions import AIProviderUnavailableError
from app.integrations.ai.mock_provider import MockAIProvider

_ANALYSIS_RESPONSE = """
Recurring mistakes:
Ошибок с повторами не найдено.

Useful vocabulary:
Попробуй "commute".

Natural alternatives:
Всё звучало естественно.

Grammar topics to review:
Present Simple.

Recommended practice:
Напиши пару предложений о своём дне.
"""


class _SequencedAIProvider:
    """Returns each response in order — start/continue/end need different
    response shapes within one test flow."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    async def complete(self, messages, *, max_tokens):
        return self._responses.pop(0)


class _UnavailableAIProvider:
    async def complete(self, messages, *, max_tokens):
        raise AIProviderUnavailableError("provider down for this test")


async def test_start_conversation_returns_opening_message(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(MockAIProvider(response="Hi! How's it going?"))

    response = await client.post(
        "/api/v1/conversation/sessions", json={"topic": "small talk"}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["topic"] == "small talk"
    assert body["ended_at"] is None
    assert body["analysis"] is None
    assert len(body["messages"]) == 1
    assert body["messages"][0]["role"] == "assistant"
    assert body["messages"][0]["content"] == "Hi! How's it going?"


async def test_start_conversation_requires_auth(client: AsyncClient, override_ai_provider):
    override_ai_provider(MockAIProvider(response="Hi!"))

    response = await client.post("/api/v1/conversation/sessions", json={})

    assert response.status_code == 401


async def test_send_message_appends_both_turns_and_returns_reply(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(_SequencedAIProvider(["Hi! How's it going?", "Nice, glad to hear!"]))

    started = await client.post("/api/v1/conversation/sessions", json={}, headers=auth_headers)
    session_id = started.json()["id"]

    response = await client.post(
        f"/api/v1/conversation/sessions/{session_id}/messages",
        json={"text": "Pretty good, thanks!"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["role"] == "assistant"
    assert response.json()["content"] == "Nice, glad to hear!"

    fetched = await client.get(f"/api/v1/conversation/sessions/{session_id}", headers=auth_headers)
    messages = fetched.json()["messages"]
    assert len(messages) == 3
    assert [m["role"] for m in messages] == ["assistant", "user", "assistant"]
    assert messages[1]["content"] == "Pretty good, thanks!"


async def test_send_message_to_ended_conversation_returns_409(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(_SequencedAIProvider(["Hi!", _ANALYSIS_RESPONSE]))

    started = await client.post("/api/v1/conversation/sessions", json={}, headers=auth_headers)
    session_id = started.json()["id"]

    ended = await client.post(
        f"/api/v1/conversation/sessions/{session_id}/end", headers=auth_headers
    )
    assert ended.status_code == 200

    response = await client.post(
        f"/api/v1/conversation/sessions/{session_id}/messages",
        json={"text": "Are you still there?"},
        headers=auth_headers,
    )
    assert response.status_code == 409


async def test_end_conversation_returns_analysis_and_is_idempotent(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(_SequencedAIProvider(["Hi!", _ANALYSIS_RESPONSE]))

    started = await client.post("/api/v1/conversation/sessions", json={}, headers=auth_headers)
    session_id = started.json()["id"]

    ended = await client.post(
        f"/api/v1/conversation/sessions/{session_id}/end", headers=auth_headers
    )
    assert ended.status_code == 200
    analysis = ended.json()["analysis"]
    assert analysis["grammar_topics_to_review"] == "Present Simple."
    assert ended.json()["ended_at"] is not None

    # Calling end again must not spend a second AI call (provider has no more
    # queued responses — if it tried, this would fail with an IndexError).
    ended_again = await client.post(
        f"/api/v1/conversation/sessions/{session_id}/end", headers=auth_headers
    )
    assert ended_again.status_code == 200
    assert ended_again.json()["analysis"] == analysis


async def test_get_unknown_conversation_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.get(
        f"/api/v1/conversation/sessions/{uuid.uuid4()}", headers=auth_headers
    )
    assert response.status_code == 404


async def test_start_conversation_returns_503_when_provider_unavailable(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(_UnavailableAIProvider())

    response = await client.post("/api/v1/conversation/sessions", json={}, headers=auth_headers)

    assert response.status_code == 503
