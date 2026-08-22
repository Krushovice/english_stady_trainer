import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LessonLockedError, LevelLockedError, NotFoundError
from app.models.learning_profile import CEFRLevel
from app.models.lesson import Lesson
from app.models.level import Level
from app.models.module import Module
from app.repositories.course_repository import CourseRepository
from app.services.lesson_progress_service import LessonProgressService
from app.services.level_exam_service import LevelExamService


class CourseService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CourseRepository(session)
        self._exams = LevelExamService(session)
        self._progress = LessonProgressService(session)

    async def list_levels(self, user_id: uuid.UUID) -> list[tuple[Level, bool]]:
        levels = await self._repo.list_levels()
        return [
            (level, await self._exams.is_level_unlocked(user_id, level.code)) for level in levels
        ]

    async def list_modules(
        self, user_id: uuid.UUID, level_code: CEFRLevel
    ) -> list[tuple[Module, bool, bool | None]]:
        if not await self._exams.is_level_unlocked(user_id, level_code):
            raise LevelLockedError(
                f"Level '{level_code.value}' is locked until the previous level's exam is passed"
            )
        modules = await self._repo.list_modules_by_level_code(level_code)

        result: list[tuple[Module, bool, bool | None]] = []
        for module in modules:
            lesson = module.lessons[0] if module.lessons else None
            if lesson is None:
                result.append((module, True, None))
                continue
            unlocked = await self._progress.is_lesson_unlocked(user_id, lesson)
            passed: bool | None = None
            if unlocked:
                completion = await self._progress.get_completion(user_id, lesson.slug)
                # `total == 0` covers both "nothing to grade" and "credited
                # via placement choice" — both mean pass without a real
                # attempt, unlike a genuinely untouched lesson (show no
                # badge yet, not a false ✕).
                shows_passed = completion.attempted or completion.total == 0
                passed = completion.passed if shows_passed else None
            result.append((module, unlocked, passed))
        return result

    async def list_lessons(self, module_slug: str) -> list[Lesson]:
        return list(await self._repo.list_lessons_by_module_slug(module_slug))

    async def get_lesson(self, user_id: uuid.UUID, lesson_slug: str) -> Lesson:
        lesson = await self._repo.get_lesson_by_slug(lesson_slug)
        if lesson is None:
            raise NotFoundError(f"Lesson '{lesson_slug}' not found")
        level = await self._repo.get_level_by_lesson_slug(lesson_slug)
        if level is not None and not await self._exams.is_level_unlocked(user_id, level.code):
            raise LevelLockedError(
                f"Level '{level.code.value}' is locked until the previous level's exam is passed"
            )
        if not await self._progress.is_lesson_unlocked(user_id, lesson):
            raise LessonLockedError(
                f"Lesson '{lesson_slug}' is locked until the previous lesson is passed"
            )
        return lesson
