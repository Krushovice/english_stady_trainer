import uuid

from httpx import AsyncClient

from app.models.lesson import Lesson


async def _get_exercise(client: AsyncClient, headers: dict[str, str], slug: str) -> dict:
    response = await client.get("/api/v1/lessons/making-small-talk/exercises", headers=headers)
    exercises = {ex["slug"]: ex for ex in response.json()}
    return exercises[slug]


async def test_list_lesson_exercises_requires_auth(
    client: AsyncClient, synced_lesson: Lesson
) -> None:
    response = await client.get("/api/v1/lessons/making-small-talk/exercises")
    assert response.status_code == 401


async def test_list_lesson_exercises_hides_answer_key(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/lessons/making-small-talk/exercises", headers=auth_headers)
    assert response.status_code == 200

    exercises = response.json()
    assert len(exercises) == 4
    for exercise in exercises:
        assert "answer_key" not in exercise
        assert "explanation" not in exercise
    slugs = {ex["slug"] for ex in exercises}
    assert "making-small-talk-mc-catch-up" in slugs


async def test_submit_correct_multiple_choice_attempt(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-mc-catch-up")

    response = await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        json={"submitted_answer": {"option_id": "b"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is True
    assert float(body["score"]) == 1.0
    assert "explanation" in body
    assert body["answer_key"] == {"correct_option_id": "b"}


async def test_submit_incorrect_attempt(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-mc-catch-up")

    response = await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        json={"submitted_answer": {"option_id": "a"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is False
    assert float(body["score"]) == 0.0


async def test_submit_partial_credit_fill_blank_attempt(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-fill-question-tags")

    response = await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        json={"submitted_answer": {"blanks": ["isn't", "wrong"]}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_correct"] is False
    assert float(body["score"]) == 0.5


async def test_submit_malformed_answer_returns_422(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-mc-catch-up")

    response = await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        json={"submitted_answer": {"wrong_field": "x"}},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_submit_attempt_on_unknown_exercise_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        f"/api/v1/exercises/{uuid.uuid4()}/attempts",
        json={"submitted_answer": {"option_id": "a"}},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_attempt_history_records_past_attempts(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-order-catch-up")

    wrong_order = {"order": ["sometime", "properly", "up", "catch", "should", "We"]}
    correct_order = {"order": ["We", "should", "catch", "up", "properly", "sometime"]}
    for option in (wrong_order, correct_order):
        r = await client.post(
            f"/api/v1/exercises/{exercise['id']}/attempts",
            json={"submitted_answer": option},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text

    response = await client.get(
        f"/api/v1/exercises/{exercise['id']}/attempts", headers=auth_headers
    )
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    assert history[0]["is_correct"] is True  # most recent attempt first


async def test_daily_quiz_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/practice/daily-quiz")
    assert response.status_code == 401


async def test_daily_quiz_is_empty_before_any_practice(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/practice/daily-quiz", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_daily_quiz_draws_from_studied_exercises(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    listing = await client.get("/api/v1/lessons/making-small-talk/exercises", headers=auth_headers)
    exercises = listing.json()
    for exercise in exercises:
        exercise_type = exercise["exercise_type"]
        if exercise_type == "multiple_choice":
            submitted = {"option_id": "a"}
        elif exercise_type == "fill_blank":
            blank_count = exercise["prompt"]["text"].count("___")
            submitted = {"blanks": ["x"] * blank_count}
        elif exercise_type == "sentence_ordering":
            submitted = {"order": exercise["prompt"]["words"]}
        else:
            submitted = {"answers": {q["id"]: "a" for q in exercise["prompt"]["questions"]}}
        r = await client.post(
            f"/api/v1/exercises/{exercise['id']}/attempts",
            json={"submitted_answer": submitted},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text

    response = await client.get("/api/v1/practice/daily-quiz", headers=auth_headers)
    assert response.status_code == 200
    quiz = response.json()
    assert 0 < len(quiz) <= 4
    studied_ids = {ex["id"] for ex in exercises}
    assert {ex["id"] for ex in quiz} <= studied_ids
    assert len({ex["id"] for ex in quiz}) == len(quiz)  # no duplicates


async def test_daily_quiz_is_stable_within_the_same_day(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-mc-catch-up")
    await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        json={"submitted_answer": {"option_id": "a"}},
        headers=auth_headers,
    )

    first = await client.get("/api/v1/practice/daily-quiz", headers=auth_headers)
    second = await client.get("/api/v1/practice/daily-quiz", headers=auth_headers)
    assert first.json() == second.json()


async def test_progress_reflects_attempts(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(
        client, auth_headers, "making-small-talk-reading-art-of-small-talk"
    )

    await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        json={"submitted_answer": {"answers": {"q1": "b", "q2": "c"}}},
        headers=auth_headers,
    )

    response = await client.get("/api/v1/progress", headers=auth_headers)
    assert response.status_code == 200
    by_skill = {row["skill"]: row for row in response.json()}
    assert "reading" in by_skill
    assert by_skill["reading"]["attempts_count"] >= 1
