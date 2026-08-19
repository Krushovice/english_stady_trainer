import uuid as uuid_module

from httpx import AsyncClient

from app.models.lesson import Lesson


async def _answer_key(exercise_id: str) -> dict:
    from app.core.db import async_session_factory
    from app.repositories.exercise_repository import ExerciseRepository

    async with async_session_factory() as session:
        exercise = await ExerciseRepository(session).get_by_id(uuid_module.UUID(exercise_id))
        return exercise.answer_key


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


async def _start_and_grade(
    client: AsyncClient, headers: dict[str, str], level: str, *, correct: bool
) -> dict:
    start = await client.post(f"/api/v1/levels/{level}/exam/attempts", headers=headers)
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
        f"/api/v1/levels/{level}/exam/attempts/{body['attempt_id']}/submit",
        json={"answers": answers},
        headers=headers,
    )
    assert submit.status_code == 200, submit.text
    return submit.json()


async def test_exam_status_requires_auth(client: AsyncClient, synced_lesson: Lesson) -> None:
    response = await client.get("/api/v1/levels/A1/exam/status")
    assert response.status_code == 401


async def test_exam_status_defaults_before_any_attempt(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/levels/A1/exam/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["exam_available"] is True
    assert body["passed"] is False
    assert body["attempts_used_in_window"] == 0
    assert body["attempts_per_window"] == 3
    assert body["cooldown_until"] is None
    assert body["in_progress_attempt_id"] is None


async def test_a2_is_locked_until_a1_exam_is_passed(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/levels/A2/modules", headers=auth_headers)
    assert response.status_code == 403


async def test_b1_stays_unlocked_since_a2_has_no_content_yet(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    """Regression guard: gating only ever looks at the immediately preceding

    level, and only if it has real content. A2 has none yet, so B1 (which
    already has real lesson content a real user relies on) must stay open.
    """
    response = await client.get("/api/v1/levels/B1/modules", headers=auth_headers)
    assert response.status_code == 200
    slugs = [module["slug"] for module in response.json()]
    assert "small-talk" in slugs


async def test_levels_response_reports_unlocked_flag(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    # Only levels with authored content have a `Level` row at all (A2/B2
    # don't exist yet) — this just checks the two that do.
    response = await client.get("/api/v1/levels", headers=auth_headers)
    assert response.status_code == 200
    by_code = {level["code"]: level for level in response.json()}
    assert by_code["A1"]["unlocked"] is True
    assert by_code["B1"]["unlocked"] is True


async def test_start_exam_attempt_returns_items_without_answer_keys(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.post("/api/v1/levels/A1/exam/attempts", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert 0 < len(body["exercises"]) <= 20
    assert "expires_at" in body
    for exercise in body["exercises"]:
        assert "answer_key" not in exercise
        assert "explanation" not in exercise


async def test_start_exam_attempt_is_idempotent_while_in_progress(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    first = await client.post("/api/v1/levels/A1/exam/attempts", headers=auth_headers)
    second = await client.post("/api/v1/levels/A1/exam/attempts", headers=auth_headers)
    assert first.json()["attempt_id"] == second.json()["attempt_id"]


async def test_submit_exam_attempt_with_all_correct_answers_passes_and_unlocks_next_level(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    result = await _start_and_grade(client, auth_headers, "A1", correct=True)
    assert result["passed"] is True
    assert result["correct_count"] == result["total_count"]

    unlocked = await client.get("/api/v1/levels/A2/modules", headers=auth_headers)
    assert unlocked.status_code == 200

    status_response = await client.get("/api/v1/levels/A1/exam/status", headers=auth_headers)
    assert status_response.json()["passed"] is True


async def test_submitting_a_passed_attempt_again_returns_409(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    start = await client.post("/api/v1/levels/A1/exam/attempts", headers=auth_headers)
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
    url = f"/api/v1/levels/A1/exam/attempts/{body['attempt_id']}/submit"
    first = await client.post(url, json={"answers": answers}, headers=auth_headers)
    assert first.status_code == 200
    second = await client.post(url, json={"answers": answers}, headers=auth_headers)
    assert second.status_code == 409


async def test_three_failed_attempts_trigger_cooldown_and_keep_next_level_locked(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    for _ in range(3):
        result = await _start_and_grade(client, auth_headers, "A1", correct=False)
        assert result["passed"] is False

    blocked = await client.post("/api/v1/levels/A1/exam/attempts", headers=auth_headers)
    assert blocked.status_code == 429

    status_response = await client.get("/api/v1/levels/A1/exam/status", headers=auth_headers)
    status_body = status_response.json()
    assert status_body["cooldown_until"] is not None
    assert status_body["attempts_used_in_window"] == 3

    still_locked = await client.get("/api/v1/levels/A2/modules", headers=auth_headers)
    assert still_locked.status_code == 403
