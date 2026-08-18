import uuid

from httpx import AsyncClient

from app.core.exceptions import AIProviderUnavailableError
from app.integrations.ai.mock_provider import MockAIProvider
from app.models.lesson import Lesson

_HOMEWORK_RESPONSE = """
Task 1:
Напиши предложение о вчерашнем дне, используя это слово.

Task 2:
Опиши свой распорядок дня в двух предложениях.

Task 3:
Напиши, чем ты обычно занимаешься по выходным.
"""

_FEEDBACK_RESPONSE = """
Good:
Хорошее предложение.

Grammar:
Ошибок не найдено.

Vocabulary:
Всё хорошо.

Natural version:
I usually go for a walk on weekends.

Try again:
Напиши ещё одно предложение о своих привычках.
"""


class _SequencedAIProvider:
    """Returns each response in order — homework generation and task
    grading need different response shapes within the same test flow, which
    the single-response `MockAIProvider` can't express."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)

    async def complete(self, messages, *, max_tokens):
        return self._responses.pop(0)


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


async def test_generate_homework_requires_studied_lesson(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    override_ai_provider(MockAIProvider(response=_HOMEWORK_RESPONSE))

    response = await client.post("/api/v1/homework/generate", headers=auth_headers)

    assert response.status_code == 404


async def test_generate_homework_requires_auth(client: AsyncClient, override_ai_provider):
    override_ai_provider(MockAIProvider(response=_HOMEWORK_RESPONSE))

    response = await client.post("/api/v1/homework/generate")

    assert response.status_code == 401


async def test_generate_homework_returns_tasks_from_studied_lesson(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(MockAIProvider(response=_HOMEWORK_RESPONSE))

    response = await client.post("/api/v1/homework/generate", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["lesson_title"] == "Making Small Talk"
    assert len(body["tasks"]) == 3
    assert body["tasks"][0]["id"] == "task-1"
    assert "вчерашнем" in body["tasks"][0]["instruction"]
    assert body["attempts"] == []


async def test_submit_homework_task_returns_feedback_and_persists(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(_SequencedAIProvider([_HOMEWORK_RESPONSE, _FEEDBACK_RESPONSE]))

    generated = await client.post("/api/v1/homework/generate", headers=auth_headers)
    homework_id = generated.json()["id"]

    submit = await client.post(
        f"/api/v1/homework/{homework_id}/tasks/task-1/submit",
        json={"text": "I go for a walk on weekend."},
        headers=auth_headers,
    )
    assert submit.status_code == 200
    body = submit.json()
    assert body["task_id"] == "task-1"
    assert body["feedback"]["natural_version"] == "I usually go for a walk on weekends."

    fetched = await client.get(f"/api/v1/homework/{homework_id}", headers=auth_headers)
    assert fetched.status_code == 200
    attempts = fetched.json()["attempts"]
    assert len(attempts) == 1
    assert attempts[0]["submitted_text"] == "I go for a walk on weekend."


async def test_submit_unknown_task_returns_404(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(MockAIProvider(response=_HOMEWORK_RESPONSE))

    generated = await client.post("/api/v1/homework/generate", headers=auth_headers)
    homework_id = generated.json()["id"]

    response = await client.post(
        f"/api/v1/homework/{homework_id}/tasks/not-a-real-task/submit",
        json={"text": "Anything."},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_get_unknown_homework_returns_404(client: AsyncClient, auth_headers: dict[str, str]):
    response = await client.get(f"/api/v1/homework/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


async def test_generate_homework_returns_503_when_provider_unavailable(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str], override_ai_provider
):
    await _study_a_lesson(client, auth_headers)
    override_ai_provider(_UnavailableAIProvider())

    response = await client.post("/api/v1/homework/generate", headers=auth_headers)

    assert response.status_code == 503
