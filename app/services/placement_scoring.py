"""Deterministic placement-test scoring and starting-module recommendation.

Pure functions, no DB access — mirrors app/services/scoring.py's separation
so the scheduling/estimation logic can be unit-tested and changed later
without touching the API or persistence layers.
"""

import uuid
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from app.models.learning_profile import CEFRLevel

# CEFR levels ordered low to high; index doubles as a numeric score for
# averaging. No C1/C2 per CLAUDE.md, so B2 is the ceiling this test can report.
LEVEL_ORDER: list[CEFRLevel] = [CEFRLevel.A1, CEFRLevel.A2, CEFRLevel.B1, CEFRLevel.B2]

# Share of items at a level that must be answered correctly to credit the
# learner with that level. CLAUDE.md: "Do not pretend the placement test can
# measure everything precisely" — this is a coarse, explainable cutoff, not a
# claim of psychometric accuracy.
PASS_THRESHOLD = 0.6


@dataclass(frozen=True)
class PlacementItemResult:
    difficulty: CEFRLevel
    is_correct: bool


def estimate_skill_level(results: Iterable[PlacementItemResult]) -> CEFRLevel | None:
    """Highest CEFR level at which the learner cleared `PASS_THRESHOLD`.

    Returns None if no items for this skill were answered — an absent
    estimate, not a fabricated default level.
    """
    by_level: dict[CEFRLevel, list[bool]] = defaultdict(list)
    for result in results:
        by_level[result.difficulty].append(result.is_correct)

    if not by_level:
        return None

    for level in reversed(LEVEL_ORDER):
        outcomes = by_level.get(level)
        if outcomes and (sum(outcomes) / len(outcomes)) >= PASS_THRESHOLD:
            return level

    return LEVEL_ORDER[0]  # attempted the test but never cleared threshold: floor at A1


def estimate_overall_level(skill_levels: Iterable[CEFRLevel | None]) -> CEFRLevel | None:
    """Overall estimate: the mean skill score, rounded down.

    Rounding down (rather than to nearest) is deliberate — same caution as
    `PASS_THRESHOLD`, prefer understating the level over overstating it.
    """
    scores = [LEVEL_ORDER.index(level) for level in skill_levels if level is not None]
    if not scores:
        return None
    average_index = sum(scores) // len(scores)
    return LEVEL_ORDER[average_index]


@dataclass(frozen=True)
class ModuleCandidate:
    id: uuid.UUID
    slug: str
    title: str
    level_code: CEFRLevel
    order_index: int


# Lightweight keyword map from a learning_profile priority goal to terms that
# might appear in a module's slug/title. Real matching, not a stub — but
# necessarily thin, since modules carry no explicit topic tags yet and
# there's only one authored module so far.
GOAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "travel": ("travel", "trip", "hotel", "airport", "direction"),
    "conversation": ("talk", "conversation", "chat", "speaking"),
    "listening_content": ("listening", "audio", "podcast"),
    "work_it": ("work", "office", "job", "colleague", "it"),
}


def recommend_modules(
    candidates: Iterable[ModuleCandidate],
    target_level: CEFRLevel | None,
    priority_goals: list[str],
) -> list[ModuleCandidate]:
    """Sort modules by: level closeness to `target_level`, then priority-goal

    keyword match (earlier goals weigh more), then natural course order.
    """
    target_index = LEVEL_ORDER.index(target_level) if target_level is not None else 0

    def goal_rank(candidate: ModuleCandidate) -> int:
        haystack = f"{candidate.slug} {candidate.title}".lower()
        for rank, goal in enumerate(priority_goals):
            keywords = GOAL_KEYWORDS.get(goal, ())
            if any(keyword in haystack for keyword in keywords):
                return rank
        return len(priority_goals)  # no match: lowest priority

    def sort_key(candidate: ModuleCandidate) -> tuple[int, int, int]:
        level_distance = abs(LEVEL_ORDER.index(candidate.level_code) - target_index)
        return (level_distance, goal_rank(candidate), candidate.order_index)

    return sorted(candidates, key=sort_key)
