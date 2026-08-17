from httpx import AsyncClient

from app.core.exceptions import AIProviderUnavailableError
from app.integrations.ai.mock_provider import MockAIProvider

_WELL_FORMED_RESPONSE = """
Good:
Nice sentence structure.

Grammar:
Use "doesn't" instead of "don't" with "she".

Vocabulary:
"very good" -> "great"

Natural version:
She doesn't like coffee.

Try again:
Write two sentences about what your friend doesn't like.
"""


class _UnavailableAIProvider:
    async def complete(self, messages, *, max_tokens):
        raise AIProviderUnavailableError("provider down for this test")


async def test_writing_feedback_returns_parsed_sections(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(MockAIProvider(response=_WELL_FORMED_RESPONSE))

    response = await client.post(
        "/api/v1/writing/feedback",
        json={"text": "She don't like coffee."},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["good"] == "Nice sentence structure."
    assert body["natural_version"] == "She doesn't like coffee."
    assert "doesn't" in body["grammar"]


async def test_writing_feedback_requires_auth(client: AsyncClient, override_ai_provider):
    override_ai_provider(MockAIProvider(response=_WELL_FORMED_RESPONSE))

    response = await client.post(
        "/api/v1/writing/feedback", json={"text": "She don't like coffee."}
    )

    assert response.status_code == 401


async def test_writing_feedback_rejects_empty_text(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(MockAIProvider(response=_WELL_FORMED_RESPONSE))

    response = await client.post(
        "/api/v1/writing/feedback", json={"text": ""}, headers=auth_headers
    )

    assert response.status_code == 422


async def test_writing_feedback_returns_503_when_provider_unavailable(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(_UnavailableAIProvider())

    response = await client.post(
        "/api/v1/writing/feedback",
        json={"text": "She don't like coffee."},
        headers=auth_headers,
    )

    assert response.status_code == 503


async def test_writing_feedback_returns_502_on_unparseable_response(
    client: AsyncClient, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(MockAIProvider(response="Sorry, I can't help with that."))

    response = await client.post(
        "/api/v1/writing/feedback",
        json={"text": "She don't like coffee."},
        headers=auth_headers,
    )

    assert response.status_code == 502
