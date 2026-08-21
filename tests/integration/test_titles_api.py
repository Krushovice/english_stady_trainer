import uuid as uuid_module

from httpx import AsyncClient

from app.models.lesson import Lesson


async def _grammar_tagged_exercise(exercises: list[dict]) -> dict | None:
    from app.core.db import async_session_factory
    from app.repositories.exercise_repository import ExerciseRepository

    async with async_session_factory() as session:
        repo = ExerciseRepository(session)
        for exercise in exercises:
            model = await repo.get_by_id(uuid_module.UUID(exercise["id"]))
            if model.grammar_topic_id is not None:
                return exercise
    return None


def _correct_submission(exercise: dict, answer_key: dict) -> dict:
    exercise_type = exercise["exercise_type"]
    if exercise_type == "multiple_choice":
        return {"option_id": answer_key["correct_option_id"]}
    if exercise_type == "fill_blank":
        return {"blanks": [group[0] for group in answer_key["blanks"]]}
    if exercise_type == "sentence_ordering":
        return {"order": answer_key["correct_order"]}
    if exercise_type == "reading_comprehension":
        return {"answers": answer_key["answers"]}
    raise ValueError(f"no correct-submission builder for exercise type '{exercise_type}'")


def _wrong_submission(exercise: dict) -> dict:
    exercise_type = exercise["exercise_type"]
    if exercise_type == "multiple_choice":
        return {"option_id": "definitely-wrong"}
    if exercise_type == "fill_blank":
        blank_count = exercise["prompt"]["text"].count("___")
        return {"blanks": ["zzz"] * blank_count}
    if exercise_type == "sentence_ordering":
        return {"order": list(reversed(exercise["prompt"]["words"]))}
    if exercise_type == "reading_comprehension":
        return {"answers": {q["id"]: "definitely-wrong" for q in exercise["prompt"]["questions"]}}
    raise ValueError(f"no wrong-submission builder for exercise type '{exercise_type}'")


async def test_get_my_title_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/titles/me")
    assert response.status_code == 401


async def test_fresh_user_gets_baseline_title(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/titles/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Новичок"
    assert body["days_practiced"] == 0
    assert body["mistakes_total"] == 0
    assert body["mistakes_mastered"] == 0
    assert body["review_count"] == 0
    assert body["cefr_grade"] == "A1"


async def test_mastering_a_topic_earns_the_debugger_title(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    exercises = (
        await client.get(
            f"/api/v1/lessons/{synced_lesson.slug}/exercises", headers=auth_headers
        )
    ).json()
    exercise = await _grammar_tagged_exercise(exercises)
    assert exercise is not None, "fixture content must include a grammar-tagged exercise"

    from app.core.db import async_session_factory
    from app.repositories.exercise_repository import ExerciseRepository

    async with async_session_factory() as session:
        answer_key = (
            await ExerciseRepository(session).get_by_id(uuid_module.UUID(exercise["id"]))
        ).answer_key

    # One wrong attempt (-> NEW), then three correct in a row (-> MASTERED,
    # MASTERY_STREAK=3 in mistake_classification.py) — this also bumps
    # review_count for the exercise's review item on every submission.
    await client.post(
        f"/api/v1/exercises/{exercise['id']}/attempts",
        headers=auth_headers,
        json={"submitted_answer": _wrong_submission(exercise)},
    )
    for _ in range(3):
        await client.post(
            f"/api/v1/exercises/{exercise['id']}/attempts",
            headers=auth_headers,
            json={"submitted_answer": _correct_submission(exercise, answer_key)},
        )

    response = await client.get("/api/v1/titles/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["mistakes_total"] == 1
    assert body["mistakes_mastered"] == 1
    assert body["review_count"] >= 4
    assert body["title"] == "Отладчик"
