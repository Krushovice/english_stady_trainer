from app.services.title_service import (
    CONFIDENT_DAYS_THRESHOLD,
    DISCIPLINE_DAYS_THRESHOLD,
    DISCIPLINE_REMEDIATION_RATIO_THRESHOLD,
    DISCIPLINE_REVIEW_COUNT_THRESHOLD,
    REGULAR_DAYS_THRESHOLD,
    REMEDIATION_RATIO_THRESHOLD,
    REVIEW_COUNT_THRESHOLD,
    TIER_CONFIDENT,
    TIER_DEBUGGER,
    TIER_DISCIPLINE,
    TIER_NEWCOMER,
    TIER_REGULAR,
    assign_tier,
)


def test_fresh_user_with_no_data_is_a_newcomer() -> None:
    assert assign_tier(0, 0, 0, 0) == TIER_NEWCOMER


def test_below_regular_days_threshold_stays_newcomer() -> None:
    assert assign_tier(REGULAR_DAYS_THRESHOLD - 1, 0, 0, 0) == TIER_NEWCOMER


def test_regular_days_threshold_reached_becomes_regular_learner() -> None:
    assert assign_tier(REGULAR_DAYS_THRESHOLD, 0, 0, 0) == TIER_REGULAR


def test_mastery_ratio_at_threshold_with_no_days_becomes_debugger() -> None:
    # 1/2 mastered clears REMEDIATION_RATIO_THRESHOLD (0.5) even with zero
    # practice days — the debugger tier is about remediation, not regularity.
    assert assign_tier(0, 1, 2, 0) == TIER_DEBUGGER


def test_zero_mistakes_total_never_qualifies_for_debugger() -> None:
    # Division-by-zero guard: no mistakes tracked yet means no remediation
    # ratio to speak of, regardless of practice days.
    assert assign_tier(DISCIPLINE_DAYS_THRESHOLD, 0, 0, DISCIPLINE_REVIEW_COUNT_THRESHOLD) in (
        TIER_REGULAR,
        TIER_NEWCOMER,
    )


def test_confident_learner_requires_all_three_signals_together() -> None:
    days = CONFIDENT_DAYS_THRESHOLD
    review_count = REVIEW_COUNT_THRESHOLD
    assert assign_tier(days, 1, 2, review_count) == TIER_CONFIDENT
    # Drop just one signal below its bar — falls back to a lower tier, not confident.
    assert assign_tier(days - 1, 1, 2, review_count) != TIER_CONFIDENT
    assert assign_tier(days, 0, 2, review_count) != TIER_CONFIDENT
    assert assign_tier(days, 1, 2, review_count - 1) != TIER_CONFIDENT


def test_iron_discipline_requires_the_highest_bar_on_all_three() -> None:
    days = DISCIPLINE_DAYS_THRESHOLD
    mastered, total = 7, 10  # ratio 0.7, exactly at DISCIPLINE_REMEDIATION_RATIO_THRESHOLD
    review_count = DISCIPLINE_REVIEW_COUNT_THRESHOLD
    assert assign_tier(days, mastered, total, review_count) == TIER_DISCIPLINE
    assert assign_tier(days - 1, mastered, total, review_count) != TIER_DISCIPLINE
    assert assign_tier(days, mastered, total, review_count - 1) != TIER_DISCIPLINE


def test_ratio_just_below_discipline_threshold_falls_back_to_confident() -> None:
    days = DISCIPLINE_DAYS_THRESHOLD
    review_count = DISCIPLINE_REVIEW_COUNT_THRESHOLD
    # ratio 0.6 clears REMEDIATION_RATIO_THRESHOLD but not the stricter
    # DISCIPLINE_REMEDIATION_RATIO_THRESHOLD (0.7).
    assert assign_tier(days, 3, 5, review_count) == TIER_CONFIDENT
    assert DISCIPLINE_REMEDIATION_RATIO_THRESHOLD > REMEDIATION_RATIO_THRESHOLD
