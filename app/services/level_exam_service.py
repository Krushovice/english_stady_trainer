"""Level exit exam: gates progression to the next CEFR level.

CLAUDE.md doesn't specify this — it's a direct product ask (2026-08-19):
finishing all of a level's lessons should be checked by a real exam before
the next level opens, not just implied by having clicked through lessons.

Design, matching what was agreed before implementation:
  - 20 questions, 70% to pass, drawn from that level's own lesson exercises
    (no separate exam content bank to author).
  - 15-minute timer per attempt.
  - Up to 3 attempts; once the most recent 3 are all failed, a 24h cooldown
    applies before a new attempt can start (a rolling window, not a
    lifetime cap — attempt 4 becomes attempt 1 of a fresh window).
  - Passing a level's exam unlocks the *next* level. A level with no
    exercises of its own (nothing authored there yet) is never gated —
    there'd be nothing to test, and gating on missing content would just
    be a bug wearing a feature's clothes. Gating only ever looks at the
    *immediately preceding* level.
  - Grandfathering: a user who has ever attempted an exercise inside a
    level already has access to it, regardless of whether the preceding
    level's exam is passed. This matters once a level that used to be
    ungated (its preceding level had no content yet) gains a gate
    retroactively — real progress must never be locked out after the
    fact. Without this, authoring A2 content would have retroactively
    locked the real user out of B1, which they'd already been studying.
  - Placement credit: choosing "start at my assessed level" after the
    placement test sets `LearningProfile.placement_skip_credit_through` —
    every level up to and including that one counts as credited (its exam
    need not be passed) for the sole purpose of unlocking the *next* level.
    See `app/services/placement_scoring.is_level_credited` and
    `PlacementService.choose_starting_point`.
"""

import random
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ExamAlreadyPassedError,
    ExamAttemptAlreadySubmittedError,
    ExamAttemptNotFoundError,
    ExamOnCooldownError,
    NotFoundError,
)
from app.models.exercise import Exercise
from app.models.exercise_attempt import AttemptSource, ExerciseAttempt
from app.models.learning_profile import CEFRLevel
from app.models.level_exam_attempt import LevelExamAttempt
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.learning_profile_repository import LearningProfileRepository
from app.repositories.level_exam_repository import LevelExamRepository
from app.services.placement_scoring import LEVEL_ORDER, is_level_credited
from app.services.scoring import InvalidSubmissionError, score_attempt

EXAM_SIZE = 20
PASS_THRESHOLD = Decimal("0.7")
DURATION_MINUTES = 15
ATTEMPTS_PER_WINDOW = 3
COOLDOWN_HOURS = 24


@dataclass(frozen=True)
class ExamStatus:
    level: CEFRLevel
    exam_available: bool  # False if the level has no exercises to draw from yet
    passed: bool
    attempts_used_in_window: int
    attempts_per_window: int
    cooldown_until: datetime | None
    in_progress: LevelExamAttempt | None


class LevelExamService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._exams = LevelExamRepository(session)
        self._exercises = ExerciseRepository(session)
        self._profiles = LearningProfileRepository(session)

    async def is_level_unlocked(self, user_id: uuid.UUID, level: CEFRLevel) -> bool:
        index = LEVEL_ORDER.index(level)
        if index == 0:
            return True
        if await self._exercises.has_any_attempt_in_level(user_id, level):
            return True
        preceding = LEVEL_ORDER[index - 1]
        profile = await self._profiles.get_by_user_id(user_id)
        if profile is not None and is_level_credited(
            preceding, profile.placement_skip_credit_through
        ):
            return True
        preceding_pool = await self._exercises.list_by_level(preceding)
        if not preceding_pool:
            return True
        return await self._exams.has_passed(user_id, preceding)

    async def get_status(self, user_id: uuid.UUID, level: CEFRLevel) -> ExamStatus:
        await self._expire_stale_attempt(user_id, level)

        pool = await self._exercises.list_by_level(level)
        passed = await self._exams.has_passed(user_id, level)
        recent = list(await self._exams.list_recent(user_id, level, limit=ATTEMPTS_PER_WINDOW))

        in_progress = next((a for a in recent if a.submitted_at is None), None)
        graded = [a for a in recent if a.submitted_at is not None]

        cooldown_until = None
        if not passed and len(graded) >= ATTEMPTS_PER_WINDOW and all(not a.passed for a in graded):
            last_attempt_at = max(a.submitted_at for a in graded if a.submitted_at is not None)
            candidate = last_attempt_at + timedelta(hours=COOLDOWN_HOURS)
            if candidate > datetime.now(UTC):
                cooldown_until = candidate

        return ExamStatus(
            level=level,
            exam_available=bool(pool),
            passed=passed,
            attempts_used_in_window=len(graded),
            attempts_per_window=ATTEMPTS_PER_WINDOW,
            cooldown_until=cooldown_until,
            in_progress=in_progress,
        )

    async def start_attempt(
        self, user_id: uuid.UUID, level: CEFRLevel
    ) -> tuple[LevelExamAttempt, list[Exercise]]:
        status = await self.get_status(user_id, level)

        if status.passed:
            raise ExamAlreadyPassedError(f"The exam for level '{level.value}' is already passed")

        if status.in_progress is not None:
            exercises = await self._load_exercises(status.in_progress.exercise_ids)
            return status.in_progress, exercises

        if status.cooldown_until is not None:
            raise ExamOnCooldownError(
                "Too many failed attempts — try again after the cooldown.",
                retry_at=status.cooldown_until,
            )

        pool = list(await self._exercises.list_by_level(level))
        if not pool:
            raise NotFoundError(f"No exam content available for level '{level.value}' yet")

        picked = _pick_round_robin_by_lesson(pool, EXAM_SIZE)
        now = datetime.now(UTC)
        attempt = LevelExamAttempt(
            user_id=user_id,
            level=level,
            exercise_ids=[str(exercise.id) for exercise in picked],
            answers={},
            expires_at=now + timedelta(minutes=DURATION_MINUTES),
        )
        await self._exams.add(attempt)
        await self._session.commit()
        return attempt, picked

    async def submit_attempt(
        self, user_id: uuid.UUID, attempt_id: uuid.UUID, answers: dict[str, dict]
    ) -> LevelExamAttempt:
        attempt = await self._exams.get_by_id(attempt_id)
        if attempt is None or attempt.user_id != user_id:
            raise ExamAttemptNotFoundError(f"Exam attempt '{attempt_id}' not found")
        if attempt.submitted_at is not None:
            raise ExamAttemptAlreadySubmittedError("This exam attempt was already graded")

        await self._grade_and_close(attempt, answers)
        await self._session.commit()
        return attempt

    # --- internals ---

    async def _expire_stale_attempt(self, user_id: uuid.UUID, level: CEFRLevel) -> None:
        recent = await self._exams.list_recent(user_id, level, limit=1)
        for attempt in recent:
            if attempt.submitted_at is None and attempt.expires_at <= datetime.now(UTC):
                await self._grade_and_close(attempt, attempt.answers)
                await self._session.commit()

    async def _grade_and_close(self, attempt: LevelExamAttempt, answers: dict[str, dict]) -> None:
        exercises = await self._load_exercises(attempt.exercise_ids)
        correct_count = 0
        for exercise in exercises:
            submitted_answer = answers.get(str(exercise.id))
            is_correct = False
            score = Decimal(0)
            if submitted_answer is not None:
                try:
                    result = score_attempt(exercise, submitted_answer)
                    is_correct = result.is_correct
                    score = result.score
                except InvalidSubmissionError:
                    pass
            if is_correct:
                correct_count += 1
            self._session.add(
                ExerciseAttempt(
                    user_id=attempt.user_id,
                    exercise_id=exercise.id,
                    submitted_answer=submitted_answer or {},
                    is_correct=is_correct,
                    score=score,
                    source=AttemptSource.LEVEL_EXAM,
                )
            )

        total = len(exercises)
        attempt.answers = answers
        attempt.score = Decimal(correct_count) / Decimal(total) if total else Decimal(0)
        attempt.passed = attempt.score >= PASS_THRESHOLD
        attempt.submitted_at = datetime.now(UTC)

    async def _load_exercises(self, exercise_ids: list[str]) -> list[Exercise]:
        by_id = {}
        for raw_id in exercise_ids:
            exercise = await self._exercises.get_by_id(uuid.UUID(raw_id))
            if exercise is not None:
                by_id[raw_id] = exercise
        return [by_id[raw_id] for raw_id in exercise_ids if raw_id in by_id]


def _pick_round_robin_by_lesson(pool: list[Exercise], size: int) -> list[Exercise]:
    rng = random.Random()
    by_lesson: dict[uuid.UUID | None, list[Exercise]] = {}
    for exercise in pool:
        by_lesson.setdefault(exercise.lesson_id, []).append(exercise)
    for group in by_lesson.values():
        rng.shuffle(group)

    lesson_ids = list(by_lesson.keys())
    rng.shuffle(lesson_ids)

    picked: list[Exercise] = []
    i = 0
    while len(picked) < size and any(by_lesson.values()):
        lesson_id = lesson_ids[i % len(lesson_ids)]
        if by_lesson[lesson_id]:
            picked.append(by_lesson[lesson_id].pop())
        i += 1
    rng.shuffle(picked)
    return picked
