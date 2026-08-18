import httpx2
import pytest
from openai import APIConnectionError

from app.core.exceptions import STTProviderUnavailableError
from app.integrations.stt.mock_provider import MockSTTProvider
from app.integrations.stt.speaches_provider import SpeachesProvider


async def test_mock_provider_returns_configured_transcript():
    provider = MockSTTProvider(transcript="Hello there.")

    result = await provider.transcribe(b"audio-bytes", "clip.wav", language="en")

    assert result == "Hello there."


async def test_mock_provider_records_calls_for_assertions():
    provider = MockSTTProvider()

    await provider.transcribe(b"audio-bytes", "clip.wav", language="en")

    assert provider.received_calls == [(b"audio-bytes", "clip.wav", "en")]


async def test_speaches_provider_wraps_connection_errors(monkeypatch):
    provider = SpeachesProvider(
        base_url="http://localhost:1/v1", api_key="x", model="m", timeout_seconds=5
    )

    async def raise_connection_error(*args, **kwargs):
        raise APIConnectionError(request=httpx2.Request("POST", "http://localhost:1/v1"))

    monkeypatch.setattr(provider._client.audio.transcriptions, "create", raise_connection_error)

    with pytest.raises(STTProviderUnavailableError):
        await provider.transcribe(b"audio-bytes", "clip.wav", language="en")
