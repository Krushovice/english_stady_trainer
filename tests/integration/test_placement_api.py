from httpx import AsyncClient

from app.models.lesson import Lesson

# Correct answers for the real placement bank (content/placement_test/bank.yaml),
# used to construct a submission that clears A1-B1 and fails B2 for
# grammar/vocabulary/reading, and clears only A1-A2 for listening — giving
# each skill a distinct, predictable estimated level.
_CORRECT_ANSWERS = {
    "placement-grammar-a1-1": {"option_id": "b"},
    "placement-grammar-a1-2": {"option_id": "c"},
    "placement-grammar-a2-1": {"blanks": ["went"]},
    "placement-grammar-a2-2": {"option_id": "b"},
    "placement-grammar-b1-1": {"blanks": ["have", "eaten"]},
    "placement-grammar-b1-2": {"option_id": "a"},
    "placement-vocabulary-a1-1": {"option_id": "a"},
    "placement-vocabulary-a1-2": {"option_id": "b"},
    "placement-vocabulary-a2-1": {"option_id": "a"},
    "placement-vocabulary-a2-2": {"option_id": "a"},
    "placement-vocabulary-b1-1": {"option_id": "a"},
    "placement-vocabulary-b1-2": {"option_id": "a"},
    "placement-reading-a1": {"answers": {"q1": "a", "q2": "a"}},
    "placement-reading-a2": {"answers": {"q1": "a", "q2": "a"}},
    "placement-reading-b1": {"answers": {"q1": "a", "q2": "a"}},
    "placement-listening-a1": {"answers": {"q1": "a", "q2": "a"}},
    "placement-listening-a2": {"answers": {"q1": "a", "q2": "a"}},
}

# Deliberately wrong, but shape-valid, submissions for every item not listed
# above (all the B2 items, plus listening B1/B2) so every item gets an
# answer — an unanswered item would just be missing data, not a real
# "wrong answer" signal.
_WRONG_ANSWERS = {
    "placement-grammar-b2-1": {"blanks": ["wrong"]},
    "placement-grammar-b2-2": {"option_id": "z"},
    "placement-vocabulary-b2-1": {"option_id": "z"},
    "placement-vocabulary-b2-2": {"option_id": "z"},
    "placement-reading-b2": {"answers": {"q1": "z", "q2": "z"}},
    "placement-listening-b1": {"answers": {"q1": "z", "q2": "z"}},
    "placement-listening-b2": {"answers": {"q1": "z", "q2": "z"}},
}


async def _submit_full_test(client: AsyncClient, headers: dict[str, str]) -> dict:
    items_response = await client.get("/api/v1/placement-test/items", headers=headers)
    answers = []
    for item in items_response.json():
        submitted = _CORRECT_ANSWERS.get(item["slug"]) or _WRONG_ANSWERS.get(item["slug"])
        assert submitted is not None, f"no answer prepared for {item['slug']}"
        answers.append({"exercise_id": item["id"], "submitted_answer": submitted})

    response = await client.post(
        "/api/v1/placement-test/submit", json={"answers": answers}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_placement_items_requires_auth(client: AsyncClient, synced_lesson: Lesson) -> None:
    response = await client.get("/api/v1/placement-test/items")
    assert response.status_code == 401


async def test_placement_items_returns_full_bank_without_answer_keys(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/placement-test/items", headers=auth_headers)
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 24
    skills = {item["skill"] for item in items}
    assert skills == {"grammar", "vocabulary", "reading", "listening"}
    for item in items:
        assert "answer_key" not in item
        assert "explanation" not in item


async def test_submit_produces_distinct_per_skill_levels(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    result = await _submit_full_test(client, auth_headers)

    levels_by_skill = {skill["skill"]: skill["level"] for skill in result["skills"]}
    assert levels_by_skill["grammar"] == "B1"
    assert levels_by_skill["vocabulary"] == "B1"
    assert levels_by_skill["reading"] == "B1"
    assert levels_by_skill["listening"] == "A2"

    # overall = floor(mean(B1=2, B1=2, B1=2, A2=1) / 4) = floor(1.75) -> index 1 -> A2
    assert result["overall_level"] == "A2"
    assert result["placement_completed_at"] is not None


async def test_submit_recommends_modules(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    result = await _submit_full_test(client, auth_headers)
    assert len(result["recommended_modules"]) >= 1
    assert {"slug", "title", "level_code"} <= result["recommended_modules"][0].keys()


async def test_result_reflects_persisted_profile_after_submit(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    await _submit_full_test(client, auth_headers)

    response = await client.get("/api/v1/placement-test/result", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()

    levels_by_skill = {skill["skill"]: skill["level"] for skill in result["skills"]}
    assert levels_by_skill["grammar"] == "B1"
    assert result["overall_level"] == "A2"
    # the read-only view doesn't recompute fresh grading stats
    assert all(skill["correct"] is None for skill in result["skills"])


async def test_result_before_any_submission_has_no_levels(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    response = await client.get("/api/v1/placement-test/result", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["skills"] == []
    assert result["overall_level"] is None
    assert result["placement_completed_at"] is None


async def test_submit_with_unknown_exercise_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/placement-test/submit",
        json={
            "answers": [
                {
                    "exercise_id": "00000000-0000-0000-0000-000000000000",
                    "submitted_answer": {"option_id": "a"},
                }
            ]
        },
        headers=auth_headers,
    )
    assert response.status_code == 404
