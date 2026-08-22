import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.exercise import Exercise, Skill
from app.models.exercise_attempt import AttemptSource, ExerciseAttempt
from app.models.learning_profile import CEFRLevel
from app.models.module import Module
from app.repositories.course_repository import CourseRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.learning_profile_repository import LearningProfileRepository
from app.services.placement_scoring import (
    LEVEL_ORDER,
    ModuleCandidate,
    PlacementItemResult,
    effective_recommendation_level,
    estimate_overall_level,
    estimate_skill_level,
    recommend_modules,
)
from app.services.scoring import InvalidSubmissionError, score_attempt

RECOMMENDED_MODULE_LIMIT = 5


@dataclass(frozen=True)
class SkillResult:
    skill: Skill
    level: CEFRLevel | None
    correct: int | None
    total: int | None


@dataclass(frozen=True)
class PlacementResult:
    overall_level: CEFRLevel | None
    skills: list[SkillResult]
    recommended_modules: list[Module]
    placement_completed_at: datetime | None


class PlacementService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._exercises = ExerciseRepository(session)
        self._course = CourseRepository(session)
        self._profiles = LearningProfileRepository(session)

    async def get_test_items(self) -> list[Exercise]:
        return list(await self._exercises.list_placement_items())

    async def submit(
        self, user_id: uuid.UUID, answers: list[tuple[uuid.UUID, dict]]
    ) -> PlacementResult:
        profile = await self._profiles.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Learning profile not found")

        results_by_skill: dict[Skill, list[PlacementItemResult]] = {}
        correct_by_skill: dict[Skill, int] = {}

        for exercise_id, submitted_answer in answers:
            exercise = await self._exercises.get_by_id(exercise_id)
            if exercise is None:
                raise NotFoundError(f"Exercise '{exercise_id}' not found")

            try:
                scored = score_attempt(exercise, submitted_answer)
            except InvalidSubmissionError:
                scored = None

            is_correct = scored is not None and scored.is_correct
            attempt = ExerciseAttempt(
                user_id=user_id,
                exercise_id=exercise_id,
                submitted_answer=submitted_answer,
                is_correct=is_correct,
                score=scored.score if scored is not None else None,
                source=AttemptSource.PLACEMENT_TEST,
            )
            await self._exercises.add_attempt(attempt)

            results_by_skill.setdefault(exercise.skill, []).append(
                PlacementItemResult(difficulty=exercise.difficulty, is_correct=is_correct)
            )
            correct_by_skill[exercise.skill] = correct_by_skill.get(exercise.skill, 0) + (
                1 if is_correct else 0
            )

        skill_levels: dict[Skill, CEFRLevel | None] = {
            skill: estimate_skill_level(results) for skill, results in results_by_skill.items()
        }
        overall_level = estimate_overall_level(skill_levels.values())

        for skill, level in skill_levels.items():
            setattr(profile, f"level_{skill.value}", level)
        now = datetime.now(UTC)
        profile.placement_completed_at = now

        await self._session.commit()

        recommended = await self._recommend_modules(
            overall_level, skill_levels.get(Skill.GRAMMAR), profile.priority_goals
        )

        skills = [
            SkillResult(
                skill=skill,
                level=level,
                correct=correct_by_skill[skill],
                total=len(results_by_skill[skill]),
            )
            for skill, level in skill_levels.items()
        ]
        return PlacementResult(
            overall_level=overall_level,
            skills=skills,
            recommended_modules=recommended,
            placement_completed_at=now,
        )

    async def get_result(self, user_id: uuid.UUID) -> PlacementResult:
        profile = await self._profiles.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Learning profile not found")

        skill_levels = {skill: getattr(profile, f"level_{skill.value}", None) for skill in Skill}
        overall_level = estimate_overall_level(skill_levels.values())
        recommended = await self._recommend_modules(
            overall_level, skill_levels.get(Skill.GRAMMAR), profile.priority_goals
        )

        # correct/total aren't meaningful here — this reads a previously
        # persisted profile, not a fresh grading pass. Left unset rather
        # than faked as 0, which would misleadingly read as "scored zero".
        skills = [
            SkillResult(skill=skill, level=level, correct=None, total=None)
            for skill, level in skill_levels.items()
            if level is not None
        ]
        return PlacementResult(
            overall_level=overall_level,
            skills=skills,
            recommended_modules=recommended,
            placement_completed_at=profile.placement_completed_at,
        )

    async def choose_starting_point(self, user_id: uuid.UUID, choice: str) -> None:
        """The post-result choice: start at the assessed level (crediting
        everything below it, no exam needed) or start over from a lower
        level for review (no state change — that level is already reachable
        under the ordinary unlock rules, e.g. A1 always is).
        """
        if choice != "assessed":
            return

        profile = await self._profiles.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Learning profile not found")

        skill_levels = {skill: getattr(profile, f"level_{skill.value}", None) for skill in Skill}
        overall_level = estimate_overall_level(skill_levels.values())
        if overall_level is None:
            return

        index = LEVEL_ORDER.index(overall_level)
        if index > 0:
            profile.placement_skip_credit_through = LEVEL_ORDER[index - 1]
            await self._session.commit()

    async def _recommend_modules(
        self,
        overall_level: CEFRLevel | None,
        grammar_level: CEFRLevel | None,
        priority_goals: list[str],
    ) -> list[Module]:
        modules = await self._course.list_all_modules()
        candidates = [
            ModuleCandidate(
                id=module.id,
                slug=module.slug,
                title=module.title,
                level_code=module.level.code,
                order_index=module.order_index,
            )
            for module in modules
        ]
        target_level = effective_recommendation_level(overall_level, grammar_level)
        ranked = recommend_modules(candidates, target_level, priority_goals)
        ranked_ids = [candidate.id for candidate in ranked[:RECOMMENDED_MODULE_LIMIT]]
        modules_by_id = {module.id: module for module in modules}
        return [modules_by_id[module_id] for module_id in ranked_ids]
