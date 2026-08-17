import httpx2
import pytest
from openai import APIConnectionError

from app.core.exceptions import AIProviderUnavailableError
from app.integrations.ai.lmstudio_provider import LMStudioProvider
from app.integrations.ai.mock_provider import MockAIProvider
from app.integrations.ai.provider import AIMessage


async def test_mock_provider_returns_configured_response():
    provider = MockAIProvider(response="Hello there.")

    result = await provider.complete([AIMessage(role="user", content="hi")], max_tokens=100)

    assert result == "Hello there."


async def test_mock_provider_records_calls_for_assertions():
    provider = MockAIProvider()
    messages = [AIMessage(role="user", content="hi")]

    await provider.complete(messages, max_tokens=100)

    assert provider.received_calls == [messages]


async def test_lmstudio_provider_wraps_connection_errors(monkeypatch):
    provider = LMStudioProvider(
        base_url="http://localhost:1/v1", api_key="x", model="m", timeout_seconds=5
    )

    async def raise_connection_error(*args, **kwargs):
        raise APIConnectionError(request=httpx2.Request("POST", "http://localhost:1/v1"))

    monkeypatch.setattr(provider._client.chat.completions, "create", raise_connection_error)

    with pytest.raises(AIProviderUnavailableError):
        await provider.complete([AIMessage(role="user", content="hi")], max_tokens=100)
