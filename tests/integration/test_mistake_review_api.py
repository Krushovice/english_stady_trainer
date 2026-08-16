import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select, update

from app.models.lesson import Lesson
from app.models.review_item import ReviewItem


async def _get_exercise(client: AsyncClient, headers: dict[str, str], slug: str) -> dict:
    response = await client.get("/api/v1/lessons/making-small-talk/exercises", headers=headers)
    exercises = {ex["slug"]: ex for ex in response.json()}
    return exercises[slug]


async def _get_user_id(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    response = await client.get("/api/v1/auth/me", headers=headers)
    return uuid.UUID(response.json()["id"])


async def _force_all_reviews_due(user_id: uuid.UUID) -> None:
    """Reviews scheduled just now are due tomorrow, not today — push them

    into the past directly in the DB so /review/due has something to list,
    without waiting for real time to pass or adding test-only API surface.
    """
    from app.core.db import async_session_factory

    async with async_session_factory() as session:
        await session.execute(
            update(ReviewItem)
            .where(ReviewItem.user_id == user_id)
            .values(due_at=datetime.now(UTC) - timedelta(days=1))
        )
        await session.commit()


async def _submit(
    client: AsyncClient, headers: dict[str, str], exercise_id: str, submitted_answer: dict
) -> None:
    response = await client.post(
        f"/api/v1/exercises/{exercise_id}/attempts",
        json={"submitted_answer": submitted_answer},
        headers=headers,
    )
    assert response.status_code == 200, response.text


async def test_correct_attempt_with_no_prior_mistake_creates_no_mistake(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-fill-question-tags")
    await _submit(client, auth_headers, exercise["id"], {"blanks": ["isn't", "have"]})

    response = await client.get("/api/v1/mistakes", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_incorrect_attempt_creates_new_mistake(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-fill-question-tags")
    await _submit(client, auth_headers, exercise["id"], {"blanks": ["wrong", "wrong"]})

    response = await client.get("/api/v1/mistakes", headers=auth_headers)
    assert response.status_code == 200
    mistakes = response.json()
    assert len(mistakes) == 1
    assert mistakes[0]["grammar_topic"]["slug"] == "question-tags"
    assert mistakes[0]["status"] == "new"
    assert mistakes[0]["total_attempts"] == 1
    assert mistakes[0]["incorrect_attempts"] == 1
    assert float(mistakes[0]["error_rate"]) == 1.0


async def test_mistake_progresses_through_repeated_improving_mastered(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-fill-question-tags")
    wrong = {"blanks": ["wrong", "wrong"]}
    right = {"blanks": ["isn't", "have"]}

    await _submit(client, auth_headers, exercise["id"], wrong)  # new
    await _submit(client, auth_headers, exercise["id"], wrong)  # repeated

    mistakes = (await client.get("/api/v1/mistakes", headers=auth_headers)).json()
    assert mistakes[0]["status"] == "repeated"

    await _submit(client, auth_headers, exercise["id"], right)  # improving (1/3 correct)
    mistakes = (await client.get("/api/v1/mistakes", headers=auth_headers)).json()
    assert mistakes[0]["status"] == "improving"

    await _submit(client, auth_headers, exercise["id"], right)  # 2/3
    await _submit(client, auth_headers, exercise["id"], right)  # 3/3 -> mastered
    mistakes = (await client.get("/api/v1/mistakes", headers=auth_headers)).json()
    assert mistakes[0]["status"] == "mastered"
    assert mistakes[0]["total_attempts"] == 5
    assert mistakes[0]["incorrect_attempts"] == 2


async def test_mistakes_filterable_by_status(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-fill-question-tags")
    await _submit(client, auth_headers, exercise["id"], {"blanks": ["wrong", "wrong"]})

    matching = await client.get("/api/v1/mistakes?status=new", headers=auth_headers)
    assert len(matching.json()) == 1

    non_matching = await client.get("/api/v1/mistakes?status=mastered", headers=auth_headers)
    assert non_matching.json() == []


async def test_mistakes_requires_auth(client: AsyncClient, synced_lesson: Lesson) -> None:
    response = await client.get("/api/v1/mistakes")
    assert response.status_code == 401


async def test_attempt_schedules_reviews_for_exercise_vocabulary_and_grammar_topic(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    # This exercise is tagged with both a grammar topic and no vocabulary;
    # the vocabulary-tagged exercise is a separate one. Use fill-question-tags
    # (grammar_topic) and mc-catch-up (vocabulary) to cover both link kinds.
    grammar_exercise = await _get_exercise(
        client, auth_headers, "making-small-talk-fill-question-tags"
    )
    vocab_exercise = await _get_exercise(client, auth_headers, "making-small-talk-mc-catch-up")

    await _submit(client, auth_headers, grammar_exercise["id"], {"blanks": ["isn't", "have"]})
    await _submit(client, auth_headers, vocab_exercise["id"], {"option_id": "b"})

    user_id = await _get_user_id(client, auth_headers)
    await _force_all_reviews_due(user_id)

    response = await client.get("/api/v1/review/due", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    item_types = {item["item_type"] for item in items}
    assert item_types == {"exercise", "grammar_topic", "vocabulary"}

    grammar_item = next(i for i in items if i["item_type"] == "grammar_topic")
    assert grammar_item["grammar_topic"]["slug"] == "question-tags"

    vocab_item = next(i for i in items if i["item_type"] == "vocabulary")
    assert vocab_item["vocabulary"]["headword"] == "catch up"

    exercise_items = [i for i in items if i["item_type"] == "exercise"]
    assert len(exercise_items) == 2  # one per distinct exercise attempted


async def test_review_due_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/review/due")
    assert response.status_code == 401


async def test_complete_review_reschedules_further_out_on_success(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercise = await _get_exercise(client, auth_headers, "making-small-talk-mc-catch-up")
    await _submit(client, auth_headers, exercise["id"], {"option_id": "b"})  # review_count -> 1

    user_id = await _get_user_id(client, auth_headers)
    review_item_id = await _first_review_item_id(user_id)

    response = await client.post(
        f"/api/v1/review/{review_item_id}/complete",
        json={"is_correct": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_count"] == 2
    assert body["interval_days"] == 6  # second correct review: 6-day interval


async def test_complete_review_on_unknown_id_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        f"/api/v1/review/{uuid.uuid4()}/complete",
        json={"is_correct": True},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def _first_review_item_id(user_id: uuid.UUID) -> uuid.UUID:
    from app.core.db import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(
            select(ReviewItem.id).where(ReviewItem.user_id == user_id).limit(1)
        )
        return result.scalar_one()
