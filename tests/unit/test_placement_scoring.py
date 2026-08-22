import uuid

from app.models.learning_profile import CEFRLevel
from app.services.placement_scoring import (
    ModuleCandidate,
    PlacementItemResult,
    effective_recommendation_level,
    estimate_overall_level,
    estimate_skill_level,
    is_level_credited,
    recommend_modules,
)


def _result(difficulty: CEFRLevel, is_correct: bool) -> PlacementItemResult:
    return PlacementItemResult(difficulty=difficulty, is_correct=is_correct)


def test_estimate_skill_level_with_no_results_returns_none() -> None:
    assert estimate_skill_level([]) is None


def test_estimate_skill_level_clears_highest_level_passed() -> None:
    results = [
        _result(CEFRLevel.A1, True),
        _result(CEFRLevel.A2, True),
        _result(CEFRLevel.B1, True),
        _result(CEFRLevel.B2, False),
    ]
    assert estimate_skill_level(results) == CEFRLevel.B1


def test_estimate_skill_level_uses_threshold_not_single_item() -> None:
    results = [
        _result(CEFRLevel.A2, True),
        _result(CEFRLevel.A2, True),
        _result(CEFRLevel.B1, True),
        _result(CEFRLevel.B1, False),  # 50% at B1, below 0.6 threshold
    ]
    assert estimate_skill_level(results) == CEFRLevel.A2


def test_estimate_skill_level_floors_at_a1_when_nothing_passes() -> None:
    results = [_result(CEFRLevel.A1, False), _result(CEFRLevel.A2, False)]
    assert estimate_skill_level(results) == CEFRLevel.A1


def test_estimate_overall_level_averages_and_rounds_down() -> None:
    # A1=0, B2=3 -> average 1.5 -> floor -> index 1 -> A2
    overall = estimate_overall_level([CEFRLevel.A1, CEFRLevel.B2])
    assert overall == CEFRLevel.A2


def test_estimate_overall_level_ignores_missing_skills() -> None:
    overall = estimate_overall_level([CEFRLevel.B1, None, CEFRLevel.B1])
    assert overall == CEFRLevel.B1


def test_estimate_overall_level_with_no_data_returns_none() -> None:
    assert estimate_overall_level([None, None]) is None


def test_effective_recommendation_level_prefers_weaker_grammar() -> None:
    # Overall B1 but grammar specifically lags at A2 -> target the weaker one.
    assert effective_recommendation_level(CEFRLevel.B1, CEFRLevel.A2) == CEFRLevel.A2


def test_effective_recommendation_level_does_not_downgrade_below_overall_unnecessarily() -> None:
    # Grammar stronger than the overall blend -> overall still the ceiling.
    assert effective_recommendation_level(CEFRLevel.A2, CEFRLevel.B1) == CEFRLevel.A2


def test_effective_recommendation_level_falls_back_to_whichever_is_present() -> None:
    assert effective_recommendation_level(None, CEFRLevel.A2) == CEFRLevel.A2
    assert effective_recommendation_level(CEFRLevel.B1, None) == CEFRLevel.B1
    assert effective_recommendation_level(None, None) is None


def test_is_level_credited_with_no_credit_set() -> None:
    assert is_level_credited(CEFRLevel.A1, None) is False


def test_is_level_credited_covers_up_to_and_including_credit_through() -> None:
    assert is_level_credited(CEFRLevel.A1, CEFRLevel.A2) is True
    assert is_level_credited(CEFRLevel.A2, CEFRLevel.A2) is True


def test_is_level_credited_does_not_cover_above_credit_through() -> None:
    assert is_level_credited(CEFRLevel.B1, CEFRLevel.A2) is False


def _module(slug: str, title: str, level: CEFRLevel, order_index: int = 1) -> ModuleCandidate:
    return ModuleCandidate(
        id=uuid.uuid4(), slug=slug, title=title, level_code=level, order_index=order_index
    )


def test_recommend_modules_prefers_matching_level() -> None:
    near = _module("small-talk", "Small Talk", CEFRLevel.B1)
    far = _module("intro", "Introduction", CEFRLevel.A1)
    result = recommend_modules([far, near], target_level=CEFRLevel.B1, priority_goals=[])
    assert result[0].slug == "small-talk"


def test_recommend_modules_prefers_priority_goal_keyword_match_at_same_level() -> None:
    talk_module = _module("small-talk", "Small Talk", CEFRLevel.B1, order_index=2)
    work_module = _module("office-life", "Office Life", CEFRLevel.B1, order_index=1)
    result = recommend_modules(
        [work_module, talk_module], target_level=CEFRLevel.B1, priority_goals=["conversation"]
    )
    assert result[0].slug == "small-talk"


def test_recommend_modules_falls_back_to_order_index() -> None:
    first = _module("aa", "AA", CEFRLevel.B1, order_index=1)
    second = _module("bb", "BB", CEFRLevel.B1, order_index=2)
    result = recommend_modules([second, first], target_level=CEFRLevel.B1, priority_goals=[])
    assert [m.slug for m in result] == ["aa", "bb"]
