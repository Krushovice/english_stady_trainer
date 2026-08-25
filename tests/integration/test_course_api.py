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
    client: AsyncClient, synced_lesson: Lesson, b1_studied_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/levels/B1/modules", headers=b1_studied_headers)
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
    client: AsyncClient, synced_lesson: Lesson, b1_studied_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/lessons/making-small-talk", headers=b1_studied_headers)
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


async def test_first_lesson_of_a_level_is_always_unlocked(
    client: AsyncClient, synced_lesson: Lesson, b1_studied_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/levels/B1/modules", headers=b1_studied_headers)
    assert response.status_code == 200
    small_talk = next(m for m in response.json() if m["slug"] == "small-talk")
    assert small_talk["unlocked"] is True


async def test_second_lesson_locked_until_first_lesson_passed(
    client: AsyncClient, synced_lesson: Lesson, b1_studied_headers: dict[str, str]
) -> None:
    # b1_studied_headers only submitted one *wrong* attempt in making-small-talk —
    # nowhere near the 70% threshold, so the next module stays locked.
    response = await client.get("/api/v1/levels/B1/modules", headers=b1_studied_headers)
    assert response.status_code == 200
    experiences = next(m for m in response.json() if m["slug"] == "experiences")
    assert experiences["unlocked"] is False
    assert experiences["passed"] is None

    lesson_response = await client.get(
        "/api/v1/lessons/talking-about-experiences", headers=b1_studied_headers
    )
    assert lesson_response.status_code == 403


async def test_second_lesson_unlocks_after_first_lesson_passed(
    client: AsyncClient, synced_lesson: Lesson, b1_lesson1_passed_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/levels/B1/modules", headers=b1_lesson1_passed_headers)
    assert response.status_code == 200
    small_talk = next(m for m in response.json() if m["slug"] == "small-talk")
    assert small_talk["unlocked"] is True
    assert small_talk["passed"] is True
    experiences = next(m for m in response.json() if m["slug"] == "experiences")
    assert experiences["unlocked"] is True

    lesson_response = await client.get(
        "/api/v1/lessons/talking-about-experiences", headers=b1_lesson1_passed_headers
    )
    assert lesson_response.status_code == 200


async def test_lesson_detail_includes_next_lesson_slug(
    client: AsyncClient, synced_lesson: Lesson, b1_lesson1_passed_headers: dict[str, str]
) -> None:
    response = await client.get(
        "/api/v1/lessons/making-small-talk", headers=b1_lesson1_passed_headers
    )
    assert response.status_code == 200
    assert response.json()["next_lesson_slug"] == "talking-about-experiences"


async def test_lesson_completion_reflects_unresolved_exercises(
    client: AsyncClient, synced_lesson: Lesson, b1_studied_headers: dict[str, str]
) -> None:
    response = await client.get(
        "/api/v1/lessons/making-small-talk/completion", headers=b1_studied_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["attempted"] is True
    assert body["passed"] is False
    assert len(body["wrong_exercise_ids"]) >= 1


async def test_lesson_completion_reflects_a_pass(
    client: AsyncClient, synced_lesson: Lesson, b1_lesson1_passed_headers: dict[str, str]
) -> None:
    response = await client.get(
        "/api/v1/lessons/making-small-talk/completion", headers=b1_lesson1_passed_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["wrong_exercise_ids"] == []
    assert body["correct"] == body["total"]
