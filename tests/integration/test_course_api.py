from httpx import AsyncClient

from app.models.lesson import Lesson


async def test_list_levels_requires_auth(client: AsyncClient, synced_lesson: Lesson) -> None:
    response = await client.get("/api/v1/levels")
    assert response.status_code == 401


async def test_list_levels_returns_seeded_level(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/levels", headers=auth_headers)
    assert response.status_code == 200
    codes = [level["code"] for level in response.json()]
    assert "B1" in codes


async def test_list_modules_for_level(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/levels/B1/modules", headers=auth_headers)
    assert response.status_code == 200
    slugs = [module["slug"] for module in response.json()]
    assert "small-talk" in slugs


async def test_list_lessons_for_module(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/modules/small-talk/lessons", headers=auth_headers)
    assert response.status_code == 200
    slugs = [lesson["slug"] for lesson in response.json()]
    assert "making-small-talk" in slugs


async def test_get_lesson_detail_includes_blocks_vocabulary_and_grammar(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/lessons/making-small-talk", headers=auth_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["slug"] == "making-small-talk"
    assert len(body["blocks"]) == 12
    assert [block["order_index"] for block in body["blocks"]] == list(range(1, 13))

    headwords = {item["headword"] for item in body["vocabulary"]}
    assert "small talk" in headwords

    grammar_slugs = {topic["slug"] for topic in body["grammar_topics"]}
    assert "question-tags" in grammar_slugs


async def test_get_lesson_not_found(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/lessons/does-not-exist", headers=auth_headers)
    assert response.status_code == 404
