import uuid

from httpx import AsyncClient

from app.core.exceptions import AIProviderUnavailableError, STTProviderUnavailableError
from app.integrations.ai.mock_provider import MockAIProvider
from app.integrations.stt.mock_provider import MockSTTProvider
from app.models.lesson import Lesson

_PROMPT_RESPONSE = "Расскажи о своём вчерашнем дне, используя Past Simple."

_FEEDBACK_RESPONSE = """
Good:
Хорошее описание дня.

Grammar:
Ошибок не найдено.

Vocabulary:
Всё хорошо.

Natural version:
Yesterday I went for a walk and read a book.

Try again:
Расскажи ещё раз, но добавь, что ты ел на завтрак.
"""


class _UnavailableSTTProvider:
    async def transcribe(self, audio, filename, *, language):
        raise STTProviderUnavailableError("STT down for this test")


class _UnavailableAIProvider:
    async def complete(self, messages, *, max_tokens):
        raise AIProviderUnavailableError("provider down for this test")


async def _study_a_lesson(client: AsyncClient, headers: dict[str, str]) -> None:
    """Submit one exercise attempt so the user has a "recently studied lesson"."""
    response = await client.get("/api/v1/lessons/making-small-talk/exercises", headers=headers)
    exercise = next(ex for ex in response.json() if ex["slug"] == "making-small-talk-mc-catch-up")
    submit = await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        json={"submitted_answer": {"option_id": "b"}},
        headers=headers,
    )
    assert submit.status_code == 200


async def test_generate_speaking_prompt_requires_studied_lesson(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(MockAIProvider(response=_PROMPT_RESPONSE))

    response = await client.post("/api/v1/speaking/prompts", headers=auth_headers)

    assert response.status_code == 404


async def test_generate_speaking_prompt_requires_auth(client: AsyncClient, override_ai_provider):
    override_ai_provider(MockAIProvider(response=_PROMPT_RESPONSE))

    response = await client.post("/api/v1/speaking/prompts")

    assert response.status_code == 401


async def test_generate_speaking_prompt_returns_attempt_from_studied_lesson(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(MockAIProvider(response=_PROMPT_RESPONSE))

    response = await client.post("/api/v1/speaking/prompts", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["lesson_title"] == "Making Small Talk"
    assert body["prompt"] == _PROMPT_RESPONSE
    assert body["transcript"] is None
    assert body["feedback"] is None
    assert body["submitted_at"] is None


async def test_submit_speaking_attempt_returns_transcript_and_feedback(
    client: AsyncClient,
    synced_lesson: Lesson,
    auth_headers: dict[str, str],
    override_ai_provider,
    override_stt_provider,
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(MockAIProvider(response=_PROMPT_RESPONSE))
    override_stt_provider(MockSTTProvider(transcript="Yesterday I go for a walk."))

    generated = await client.post("/api/v1/speaking/prompts", headers=auth_headers)
    attempt_id = generated.json()["id"]

    override_ai_provider(MockAIProvider(response=_FEEDBACK_RESPONSE))
    submit = await client.post(
        f"/api/v1/speaking/attempts/{attempt_id}/submit",
        files={"audio": ("clip.wav", b"fake-audio-bytes", "audio/wav")},
        headers=auth_headers,
    )

    assert submit.status_code == 200
    body = submit.json()
    assert body["transcript"] == "Yesterday I go for a walk."
    assert body["feedback"]["natural_version"] == "Yesterday I went for a walk and read a book."
    assert body["submitted_at"] is not None

    fetched = await client.get(f"/api/v1/speaking/attempts/{attempt_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["transcript"] == "Yesterday I go for a walk."


async def test_submit_speaking_attempt_twice_returns_409(
    client: AsyncClient,
    synced_lesson: Lesson,
    auth_headers: dict[str, str],
    override_ai_provider,
    override_stt_provider,
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(MockAIProvider(response=_PROMPT_RESPONSE))
    override_stt_provider(MockSTTProvider(transcript="Something."))

    generated = await client.post("/api/v1/speaking/prompts", headers=auth_headers)
    attempt_id = generated.json()["id"]

    override_ai_provider(MockAIProvider(response=_FEEDBACK_RESPONSE))
    first = await client.post(
        f"/api/v1/speaking/attempts/{attempt_id}/submit",
        files={"audio": ("clip.wav", b"fake-audio-bytes", "audio/wav")},
        headers=auth_headers,
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/v1/speaking/attempts/{attempt_id}/submit",
        files={"audio": ("clip.wav", b"fake-audio-bytes", "audio/wav")},
        headers=auth_headers,
    )
    assert second.status_code == 409


async def test_submit_speaking_attempt_with_silent_audio_returns_422(
    client: AsyncClient,
    synced_lesson: Lesson,
    auth_headers: dict[str, str],
    override_ai_provider,
    override_stt_provider,
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(MockAIProvider(response=_PROMPT_RESPONSE))
    override_stt_provider(MockSTTProvider(transcript="   "))

    generated = await client.post("/api/v1/speaking/prompts", headers=auth_headers)
    attempt_id = generated.json()["id"]

    response = await client.post(
        f"/api/v1/speaking/attempts/{attempt_id}/submit",
        files={"audio": ("clip.wav", b"fake-audio-bytes", "audio/wav")},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_submit_speaking_attempt_returns_503_when_stt_unavailable(
    client: AsyncClient,
    synced_lesson: Lesson,
    auth_headers: dict[str, str],
    override_ai_provider,
    override_stt_provider,
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(MockAIProvider(response=_PROMPT_RESPONSE))
    override_stt_provider(MockSTTProvider(transcript="placeholder"))

    generated = await client.post("/api/v1/speaking/prompts", headers=auth_headers)
    attempt_id = generated.json()["id"]

    override_stt_provider(_UnavailableSTTProvider())
    response = await client.post(
        f"/api/v1/speaking/attempts/{attempt_id}/submit",
        files={"audio": ("clip.wav", b"fake-audio-bytes", "audio/wav")},
        headers=auth_headers,
    )
    assert response.status_code == 503


async def test_get_unknown_speaking_attempt_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.get(f"/api/v1/speaking/attempts/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


async def test_start_lesson_speaking_attempt_uses_the_lesson_authored_prompt(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
):
    response = await client.post(
        "/api/v1/speaking/lessons/making-small-talk/attempts", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["lesson_title"] == "Making Small Talk"
    assert body["prompt"].startswith("Imagine you're at a work event")
    assert body["transcript"] is None
    assert body["submitted_at"] is None


async def test_start_lesson_speaking_attempt_requires_auth(
    client: AsyncClient, synced_lesson: Lesson
):
    response = await client.post("/api/v1/speaking/lessons/making-small-talk/attempts")

    assert response.status_code == 401


async def test_start_lesson_speaking_attempt_for_unknown_lesson_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
):
    response = await client.post(
        "/api/v1/speaking/lessons/does-not-exist/attempts", headers=auth_headers
    )

    assert response.status_code == 404


async def test_start_lesson_speaking_attempt_can_then_be_submitted(
    client: AsyncClient,
    synced_lesson: Lesson,
    auth_headers: dict[str, str],
    override_ai_provider,
    override_stt_provider,
):
    generated = await client.post(
        "/api/v1/speaking/lessons/making-small-talk/attempts", headers=auth_headers
    )
    attempt_id = generated.json()["id"]

    override_stt_provider(MockSTTProvider(transcript="Hi, how's it going tonight?"))
    override_ai_provider(MockAIProvider(response=_FEEDBACK_RESPONSE))
    submit = await client.post(
        f"/api/v1/speaking/attempts/{attempt_id}/submit",
        files={"audio": ("clip.wav", b"fake-audio-bytes", "audio/wav")},
        headers=auth_headers,
    )

    assert submit.status_code == 200
    assert submit.json()["transcript"] == "Hi, how's it going tonight?"


async def test_generate_speaking_prompt_returns_503_when_provider_unavailable(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(_UnavailableAIProvider())

    response = await client.post("/api/v1/speaking/prompts", headers=auth_headers)

    assert response.status_code == 503
