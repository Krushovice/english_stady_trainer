"""Course-wide final exam: the 5th exam, gating the completion certificate.

Separate from LevelExamService's per-level exit exams (A1/A2/B1/B2), which
stay as-is. Direct product ask (2026-08-20, see docs/decisions.md "Course-wide
final exam"): on top of the 4 existing per-level exams, one more exam covering
the *whole* course — 40-50 questions drawn from all four levels, ordered
easy → hard — gates the certificate specifically.

Reuses LevelExamService's pass/timer/cooldown parameters as-is (the user's
own framing: "reuse the existing level-exam parameters unless asked
otherwise") and its `_pick_round_robin_by_lesson` helper for diversifying
within a difficulty tier — imported directly rather than duplicated, since
CLAUDE.md warns against duplicated business logic.
"""

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
    LevelLockedError,
    NotFoundError,
)
from app.models.course_exam_attempt import CourseExamAttempt
from app.models.exercise import Exercise
from app.models.exercise_attempt import AttemptSource, ExerciseAttempt
from app.models.learning_profile import CEFRLevel
from app.repositories.course_exam_repository import CourseExamRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.level_exam_repository import LevelExamRepository
from app.services.level_exam_service import (
    ATTEMPTS_PER_WINDOW,
    COOLDOWN_HOURS,
    DURATION_MINUTES,
    PASS_THRESHOLD,
    _pick_round_robin_by_lesson,
)
from app.services.placement_scoring import LEVEL_ORDER
from app.services.scoring import InvalidSubmissionError, score_attempt

# 40-50 range per the user's spec; divisible by 4 difficulty tiers so each
# tier's share is exact with no remainder to distribute.
EXAM_SIZE = 44


@dataclass(frozen=True)
class CourseExamStatus:
    exam_available: bool  # False if not yet eligible (B2 exit exam not passed)
    passed: bool
    attempts_used_in_window: int
    attempts_per_window: int
    cooldown_until: datetime | None
    in_progress: CourseExamAttempt | None
    certificate_available: bool
    earned_at: datetime | None


class CourseExamService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._exams = CourseExamRepository(session)
        self._exercises = ExerciseRepository(session)
        self._level_exams = LevelExamRepository(session)

    async def is_eligible(self, user_id: uuid.UUID) -> bool:
        """The B2 exit exam must be passed before the course-wide exam
        makes sense as a genuine whole-course assessment — otherwise the
        question pool could be thin or absent on the hardest level."""
        return await self._level_exams.has_passed(user_id, CEFRLevel.B2)

    async def get_status(self, user_id: uuid.UUID) -> CourseExamStatus:
        await self._expire_stale_attempt(user_id)

        eligible = await self.is_eligible(user_id)
        passed_attempt = await self._exams.get_passed_attempt(user_id)
        recent = list(await self._exams.list_recent(user_id, limit=ATTEMPTS_PER_WINDOW))

        in_progress = next((a for a in recent if a.submitted_at is None), None)
        graded = [a for a in recent if a.submitted_at is not None]

        cooldown_until = None
        passed = passed_attempt is not None
        if not passed and len(graded) >= ATTEMPTS_PER_WINDOW and all(not a.passed for a in graded):
            last_attempt_at = max(a.submitted_at for a in graded if a.submitted_at is not None)
            candidate = last_attempt_at + timedelta(hours=COOLDOWN_HOURS)
            if candidate > datetime.now(UTC):
                cooldown_until = candidate

        return CourseExamStatus(
            exam_available=eligible,
            passed=passed,
            attempts_used_in_window=len(graded),
            attempts_per_window=ATTEMPTS_PER_WINDOW,
            cooldown_until=cooldown_until,
            in_progress=in_progress,
            certificate_available=passed,
            earned_at=passed_attempt.submitted_at if passed_attempt else None,
        )

    async def start_attempt(
        self, user_id: uuid.UUID
    ) -> tuple[CourseExamAttempt, list[Exercise]]:
        status = await self.get_status(user_id)

        if not status.exam_available:
            raise LevelLockedError("Pass the B2 exit exam before attempting the final exam")

        if status.passed:
            raise ExamAlreadyPassedError("The course-wide final exam is already passed")

        if status.in_progress is not None:
            exercises = await self._load_exercises(status.in_progress.exercise_ids)
            return status.in_progress, exercises

        if status.cooldown_until is not None:
            raise ExamOnCooldownError(
                "Too many failed attempts — try again after the cooldown.",
                retry_at=status.cooldown_until,
            )

        pool = list(await self._exercises.list_all_non_placement())
        if not pool:
            raise NotFoundError("No exam content available yet")

        picked = _pick_easy_to_hard(pool, EXAM_SIZE)
        now = datetime.now(UTC)
        attempt = CourseExamAttempt(
            user_id=user_id,
            exercise_ids=[str(exercise.id) for exercise in picked],
            answers={},
            expires_at=now + timedelta(minutes=DURATION_MINUTES),
        )
        await self._exams.add(attempt)
        await self._session.commit()
        return attempt, picked

    async def submit_attempt(
        self, user_id: uuid.UUID, attempt_id: uuid.UUID, answers: dict[str, dict]
    ) -> CourseExamAttempt:
        attempt = await self._exams.get_by_id(attempt_id)
        if attempt is None or attempt.user_id != user_id:
            raise ExamAttemptNotFoundError(f"Exam attempt '{attempt_id}' not found")
        if attempt.submitted_at is not None:
            raise ExamAttemptAlreadySubmittedError("This exam attempt was already graded")

        await self._grade_and_close(attempt, answers)
        await self._session.commit()
        return attempt

    # --- internals ---

    async def _expire_stale_attempt(self, user_id: uuid.UUID) -> None:
        recent = await self._exams.list_recent(user_id, limit=1)
        for attempt in recent:
            if attempt.submitted_at is None and attempt.expires_at <= datetime.now(UTC):
                await self._grade_and_close(attempt, attempt.answers)
                await self._session.commit()

    async def _grade_and_close(self, attempt: CourseExamAttempt, answers: dict[str, dict]) -> None:
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
                    source=AttemptSource.FINAL_EXAM,
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


def _pick_easy_to_hard(pool: list[Exercise], size: int) -> list[Exercise]:
    """Split the pool into 4 buckets by `Exercise.difficulty`, diversify
    within each bucket by lesson (reusing `_pick_round_robin_by_lesson`),
    then concatenate the buckets in ascending `LEVEL_ORDER` — A1 → A2 → B1
    → B2 — with NO shuffle after concatenating. That ordering IS the
    "easy → hard" requirement; shuffling afterward would destroy it.

    If a bucket has fewer exercises than its even share, whatever's
    available is taken and the shortfall is not redistributed to other
    buckets — kept simple since the course currently has ample content
    across all 4 levels (see docs/roadmap.md).
    """
    by_difficulty: dict[CEFRLevel, list[Exercise]] = {level: [] for level in LEVEL_ORDER}
    for exercise in pool:
        by_difficulty[exercise.difficulty].append(exercise)

    base = size // len(LEVEL_ORDER)
    remainder = size % len(LEVEL_ORDER)
    shares = [base + (1 if i < remainder else 0) for i in range(len(LEVEL_ORDER))]

    picked: list[Exercise] = []
    for level, share in zip(LEVEL_ORDER, shares, strict=True):
        picked.extend(_pick_round_robin_by_lesson(by_difficulty[level], share))
    return picked
