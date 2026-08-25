import httpx2
import pytest
from openai import APIConnectionError

from app.core.exceptions import TTSProviderUnavailableError
from app.integrations.tts.kokoro_provider import KokoroTTSProvider
from app.integrations.tts.mock_provider import MockTTSProvider


async def test_mock_provider_returns_configured_audio():
    provider = MockTTSProvider(audio=b"fake-mp3-bytes")

    result = await provider.synthesize("Hello there.")

    assert result == b"fake-mp3-bytes"


async def test_mock_provider_records_calls_for_assertions():
    provider = MockTTSProvider()

    await provider.synthesize("Hello there.")

    assert provider.received_calls == [("Hello there.", None)]


async def test_mock_provider_records_the_requested_voice():
    provider = MockTTSProvider()

    await provider.synthesize("Hello there.", voice="am_adam")

    assert provider.received_calls == [("Hello there.", "am_adam")]


async def test_kokoro_provider_uses_configured_voice_by_default(monkeypatch):
    provider = KokoroTTSProvider(
        base_url="http://localhost:1/v1", api_key="x", voice="af_bella", timeout_seconds=5
    )
    calls = []

    class FakeResponse:
        async def aread(self):
            return b"audio"

    async def fake_create(**kwargs):
        calls.append(kwargs["voice"])
        return FakeResponse()

    monkeypatch.setattr(provider._client.audio.speech, "create", fake_create)

    await provider.synthesize("Hello there.")
    await provider.synthesize("Hi again.", voice="am_adam")

    assert calls == ["af_bella", "am_adam"]


async def test_kokoro_provider_wraps_connection_errors(monkeypatch):
    provider = KokoroTTSProvider(
        base_url="http://localhost:1/v1", api_key="x", voice="af_bella", timeout_seconds=5
    )

    async def raise_connection_error(*args, **kwargs):
        raise APIConnectionError(request=httpx2.Request("POST", "http://localhost:1/v1"))

    monkeypatch.setattr(provider._client.audio.speech, "create", raise_connection_error)

    with pytest.raises(TTSProviderUnavailableError):
        await provider.synthesize("Hello there.")
