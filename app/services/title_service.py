"""Personal-cabinet title/grade: one "main" title computed from data the
app already tracks, no new tracking tables.

CLAUDE.md's MVP scope flags "complex gamification" as out of scope but the
user explicitly asked for grades/titles (2026-08-19, see docs/decisions.md
"Titles/grades + certificate"). The compromise landed there: a single title
at a time, not a wall of badges, always shown together with the raw stats
that produced it — CLAUDE.md: "avoid showing users meaningless statistics."

Three signals feed the tier ladder:
  - Regularity: distinct calendar days with an ExerciseAttempt.
  - Mistake remediation: fraction of mistake-tracked grammar topics that
    reached MASTERED (app/services/mistake_classification.py's state
    machine already captures "was wrong, now getting it right").
  - Review consistency: lifetime sum of ReviewItem.review_count.

The two highest tiers require all three signals to clear their threshold
together, so a title can't be earned by gaming one axis alone.
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_profile import CEFRLevel
from app.models.user_mistake import MistakeStatus
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.review_repository import ReviewRepository
from app.services.level_exam_service import LevelExamService
from app.services.placement_scoring import LEVEL_ORDER

# --- tier thresholds, each independently named and justified ---

REGULAR_DAYS_THRESHOLD = 5  # a school week's worth of distinct practice days
CONFIDENT_DAYS_THRESHOLD = 10
DISCIPLINE_DAYS_THRESHOLD = 20

# mastered / total mistake-tracked topics
REMEDIATION_RATIO_THRESHOLD = Decimal("0.5")
DISCIPLINE_REMEDIATION_RATIO_THRESHOLD = Decimal("0.7")

REVIEW_COUNT_THRESHOLD = 15
DISCIPLINE_REVIEW_COUNT_THRESHOLD = 30

TIER_NEWCOMER = "Новичок"
TIER_REGULAR = "Постоянный ученик"
TIER_DEBUGGER = "Отладчик"
TIER_CONFIDENT = "Уверенный ученик"
TIER_DISCIPLINE = "Железная дисциплина"


def _mastery_ratio(mastered: int, total: int) -> Decimal:
    if total == 0:
        return Decimal(0)
    return Decimal(mastered) / Decimal(total)


def assign_tier(
    days_practiced: int, mistakes_mastered: int, mistakes_total: int, review_count: int
) -> str:
    """Pure function, no DB access — checked hardest tier first, same
    "highest that clears the bar" shape as placement_scoring's per-skill
    estimate."""
    ratio = _mastery_ratio(mistakes_mastered, mistakes_total)

    if (
        days_practiced >= DISCIPLINE_DAYS_THRESHOLD
        and ratio >= DISCIPLINE_REMEDIATION_RATIO_THRESHOLD
        and review_count >= DISCIPLINE_REVIEW_COUNT_THRESHOLD
    ):
        return TIER_DISCIPLINE

    if (
        days_practiced >= CONFIDENT_DAYS_THRESHOLD
        and ratio >= REMEDIATION_RATIO_THRESHOLD
        and review_count >= REVIEW_COUNT_THRESHOLD
    ):
        return TIER_CONFIDENT

    if mistakes_total > 0 and ratio >= REMEDIATION_RATIO_THRESHOLD:
        return TIER_DEBUGGER

    if days_practiced >= REGULAR_DAYS_THRESHOLD:
        return TIER_REGULAR

    return TIER_NEWCOMER


@dataclass(frozen=True)
class TitleResult:
    title: str
    cefr_grade: CEFRLevel | None
    days_practiced: int
    mistakes_mastered: int
    mistakes_total: int
    review_count: int


class TitleService:
    def __init__(self, session: AsyncSession) -> None:
        self._exercises = ExerciseRepository(session)
        self._mistakes = MistakeRepository(session)
        self._reviews = ReviewRepository(session)
        self._level_exams = LevelExamService(session)

    async def get_title(self, user_id: uuid.UUID) -> TitleResult:
        days_practiced = await self._exercises.count_distinct_attempt_days(user_id)
        status_counts = await self._mistakes.count_by_status(user_id)
        mistakes_mastered = status_counts[MistakeStatus.MASTERED]
        mistakes_total = sum(status_counts.values())
        review_count = await self._reviews.sum_review_count(user_id)
        cefr_grade = await self._current_cefr_grade(user_id)

        title = assign_tier(days_practiced, mistakes_mastered, mistakes_total, review_count)

        return TitleResult(
            title=title,
            cefr_grade=cefr_grade,
            days_practiced=days_practiced,
            mistakes_mastered=mistakes_mastered,
            mistakes_total=mistakes_total,
            review_count=review_count,
        )

    async def _current_cefr_grade(self, user_id: uuid.UUID) -> CEFRLevel | None:
        """Highest CEFR level the user currently has *unlocked*.

        Deliberate choice over two other plausible readings:
          - LearningProfile.level_* (placement-time snapshot) never
            advances after onboarding, so it would freeze the grade at
            whatever the user tested into once.
          - "Highest exam *passed*" (LevelExamRepository.has_passed) would
            understate a grandfathered user's real position — the
            grandfathering rule in LevelExamService.is_level_unlocked can
            unlock a level via prior attempts without a passed exam (see
            docs/decisions.md's grandfathering entry), and that access is
            exactly what a "current grade" should reflect.
        """
        grade: CEFRLevel | None = None
        for level in LEVEL_ORDER:
            if await self._level_exams.is_level_unlocked(user_id, level):
                grade = level
        return grade
