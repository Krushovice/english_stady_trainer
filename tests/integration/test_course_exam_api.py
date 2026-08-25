import uuid as uuid_module

from httpx import AsyncClient

from app.models.lesson import Lesson

_LEVEL_ORDER = ["A1", "A2", "B1", "B2"]


async def _answer_key(exercise_id: str) -> dict:
    from app.core.db import async_session_factory
    from app.repositories.exercise_repository import ExerciseRepository

    async with async_session_factory() as session:
        exercise = await ExerciseRepository(session).get_by_id(uuid_module.UUID(exercise_id))
        return exercise.answer_key


async def _difficulty(exercise_id: str) -> str:
    from app.core.db import async_session_factory
    from app.repositories.exercise_repository import ExerciseRepository

    async with async_session_factory() as session:
        exercise = await ExerciseRepository(session).get_by_id(uuid_module.UUID(exercise_id))
        return exercise.difficulty.value


def _correct_submission(exercise: dict, answer_key: dict) -> dict:
    exercise_type = exercise["exercise_type"]
    if exercise_type == "multiple_choice":
        return {"option_id": answer_key["correct_option_id"]}
    if exercise_type == "fill_blank":
        return {"blanks": [group[0] for group in answer_key["blanks"]]}
    if exercise_type == "sentence_ordering":
        return {"order": answer_key["correct_order"]}
    if exercise_type in ("reading_comprehension", "listening_comprehension"):
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
    if exercise_type in ("reading_comprehension", "listening_comprehension"):
        return {"answers": {q["id"]: "definitely-wrong" for q in exercise["prompt"]["questions"]}}
    raise ValueError(f"no wrong-submission builder for exercise type '{exercise_type}'")


async def _start_and_grade(client: AsyncClient, headers: dict[str, str], *, correct: bool) -> dict:
    start = await client.post("/api/v1/course-exam/attempts", headers=headers)
    assert start.status_code == 200, start.text
    body = start.json()

    answers = []
    for exercise in body["exercises"]:
        if correct:
            answer_key = await _answer_key(exercise["id"])
            submitted = _correct_submission(exercise, answer_key)
        else:
            submitted = _wrong_submission(exercise)
        answers.append({"exercise_id": exercise["id"], "submitted_answer": submitted})

    submit = await client.post(
        f"/api/v1/course-exam/attempts/{body['attempt_id']}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert submit.status_code == 200, submit.text
    return submit.json()


async def test_course_exam_status_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/course-exam/status")
    assert response.status_code == 401


async def test_status_shows_unavailable_before_b2_is_passed(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/course-exam/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["exam_available"] is False
    assert body["certificate_available"] is False


async def test_start_before_b2_is_passed_returns_403(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.post("/api/v1/course-exam/attempts", headers=auth_headers)
    assert response.status_code == 403


async def test_start_returns_questions_ordered_easy_to_hard(
    client: AsyncClient, synced_lesson: Lesson, b2_passed_headers: dict[str, str]
) -> None:
    response = await client.post("/api/v1/course-exam/attempts", headers=b2_passed_headers)
    assert response.status_code == 200
    body = response.json()
    assert 40 <= len(body["exercises"]) <= 50
    for exercise in body["exercises"]:
        assert "answer_key" not in exercise
        assert "explanation" not in exercise

    difficulties = [await _difficulty(exercise["id"]) for exercise in body["exercises"]]
    difficulty_ranks = [_LEVEL_ORDER.index(d) for d in difficulties]
    assert difficulty_ranks == sorted(difficulty_ranks)


async def test_start_attempt_is_idempotent_while_in_progress(
    client: AsyncClient, synced_lesson: Lesson, b2_passed_headers: dict[str, str]
) -> None:
    first = await client.post("/api/v1/course-exam/attempts", headers=b2_passed_headers)
    second = await client.post("/api/v1/course-exam/attempts", headers=b2_passed_headers)
    assert first.json()["attempt_id"] == second.json()["attempt_id"]


async def test_passing_unlocks_the_certificate(
    client: AsyncClient, synced_lesson: Lesson, b2_passed_headers: dict[str, str]
) -> None:
    result = await _start_and_grade(client, b2_passed_headers, correct=True)
    assert result["passed"] is True
    assert result["correct_count"] == result["total_count"]

    status_response = await client.get("/api/v1/course-exam/status", headers=b2_passed_headers)
    status_body = status_response.json()
    assert status_body["passed"] is True
    assert status_body["certificate_available"] is True
    assert status_body["earned_at"] is not None


async def test_submitting_a_passed_attempt_again_returns_409(
    client: AsyncClient, synced_lesson: Lesson, b2_passed_headers: dict[str, str]
) -> None:
    start = await client.post("/api/v1/course-exam/attempts", headers=b2_passed_headers)
    body = start.json()
    answers = []
    for exercise in body["exercises"]:
        answer_key = await _answer_key(exercise["id"])
        answers.append(
            {
                "exercise_id": exercise["id"],
                "submitted_answer": _correct_submission(exercise, answer_key),
            }
        )
    url = f"/api/v1/course-exam/attempts/{body['attempt_id']}/submit"
    first = await client.post(url, json={"answers": answers}, headers=b2_passed_headers)
    assert first.status_code == 200
    second = await client.post(url, json={"answers": answers}, headers=b2_passed_headers)
    assert second.status_code == 409


async def test_three_failed_attempts_trigger_cooldown(
    client: AsyncClient, synced_lesson: Lesson, b2_passed_headers: dict[str, str]
) -> None:
    for _ in range(3):
        result = await _start_and_grade(client, b2_passed_headers, correct=False)
        assert result["passed"] is False

    blocked = await client.post("/api/v1/course-exam/attempts", headers=b2_passed_headers)
    assert blocked.status_code == 429

    status_response = await client.get("/api/v1/course-exam/status", headers=b2_passed_headers)
    status_body = status_response.json()
    assert status_body["cooldown_until"] is not None
    assert status_body["attempts_used_in_window"] == 3
