import uuid

from httpx import AsyncClient

from app.models.lesson import Lesson


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "correcthorsebattery"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_list_levels_requires_auth(client: AsyncClient, synced_lesson: Lesson) -> None:
    response = await client.get("/api/v1/levels")
    assert response.status_code == 401


async def test_list_levels_returns_seeded_level(client: AsyncClient, synced_lesson: Lesson) -> None:
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/levels", headers=headers)
    assert response.status_code == 200
    codes = [level["code"] for level in response.json()]
    assert "B1" in codes


async def test_list_modules_for_level(client: AsyncClient, synced_lesson: Lesson) -> None:
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/levels/B1/modules", headers=headers)
    assert response.status_code == 200
    slugs = [module["slug"] for module in response.json()]
    assert "small-talk" in slugs


async def test_list_lessons_for_module(client: AsyncClient, synced_lesson: Lesson) -> None:
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/modules/small-talk/lessons", headers=headers)
    assert response.status_code == 200
    slugs = [lesson["slug"] for lesson in response.json()]
    assert "making-small-talk" in slugs


async def test_get_lesson_detail_includes_blocks_vocabulary_and_grammar(
    client: AsyncClient, synced_lesson: Lesson
) -> None:
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/lessons/making-small-talk", headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert body["slug"] == "making-small-talk"
    assert len(body["blocks"]) == 11
    assert [block["order_index"] for block in body["blocks"]] == list(range(1, 12))

    headwords = {item["headword"] for item in body["vocabulary"]}
    assert "small talk" in headwords

    grammar_slugs = {topic["slug"] for topic in body["grammar_topics"]}
    assert "question-tags" in grammar_slugs


async def test_get_lesson_not_found(client: AsyncClient, synced_lesson: Lesson) -> None:
    headers = await _auth_headers(client)
    response = await client.get("/api/v1/lessons/does-not-exist", headers=headers)
    assert response.status_code == 404
