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


async def test_choose_assessed_credits_levels_below_the_assessed_one(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    # _submit_full_test's known answers produce overall_level == "A2" (see
    # test_submit_produces_distinct_per_skill_levels) — so "assessed" should
    # credit through A1, unlocking A2 without a real A1 attempt or exam.
    result = await _submit_full_test(client, auth_headers)
    assert result["overall_level"] == "A2"

    choose = await client.post(
        "/api/v1/placement-test/choose-starting-point",
        json={"choice": "assessed"},
        headers=auth_headers,
    )
    assert choose.status_code == 204

    levels = (await client.get("/api/v1/levels", headers=auth_headers)).json()
    unlocked_by_code = {level["code"]: level["unlocked"] for level in levels}
    assert unlocked_by_code["A1"] is True
    assert unlocked_by_code["A2"] is True
    assert unlocked_by_code["B1"] is False

    # A1 is credited (below the assessed level) -> its lessons are auto-passed.
    a1_modules = (await client.get("/api/v1/levels/A1/modules", headers=auth_headers)).json()
    assert all(module["unlocked"] and module["passed"] for module in a1_modules)

    # A2 is the assessed level itself -> unlocked to enter, but still has to
    # be studied lesson by lesson, not auto-credited.
    a2_modules = (await client.get("/api/v1/levels/A2/modules", headers=auth_headers)).json()
    first, second = a2_modules[0], a2_modules[1]
    assert first["unlocked"] is True
    assert first["passed"] is None
    assert second["unlocked"] is False


async def test_choose_review_leaves_unlock_state_unchanged(
    client: AsyncClient, synced_lesson: Lesson, auth_headers: dict[str, str]
) -> None:
    result = await _submit_full_test(client, auth_headers)
    assert result["overall_level"] == "A2"

    choose = await client.post(
        "/api/v1/placement-test/choose-starting-point",
        json={"choice": "review"},
        headers=auth_headers,
    )
    assert choose.status_code == 204

    levels = (await client.get("/api/v1/levels", headers=auth_headers)).json()
    unlocked_by_code = {level["code"]: level["unlocked"] for level in levels}
    assert unlocked_by_code["A1"] is True
    assert unlocked_by_code["A2"] is False


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
