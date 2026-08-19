import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LevelLockedError, NotFoundError
from app.models.learning_profile import CEFRLevel
from app.models.lesson import Lesson
from app.models.level import Level
from app.models.module import Module
from app.repositories.course_repository import CourseRepository
from app.services.level_exam_service import LevelExamService


class CourseService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CourseRepository(session)
        self._exams = LevelExamService(session)

    async def list_levels(self, user_id: uuid.UUID) -> list[tuple[Level, bool]]:
        levels = await self._repo.list_levels()
        return [(level, await self._exams.is_level_unlocked(user_id, level.code)) for level in levels]

    async def list_modules(self, user_id: uuid.UUID, level_code: CEFRLevel) -> list[Module]:
        if not await self._exams.is_level_unlocked(user_id, level_code):
            raise LevelLockedError(
                f"Level '{level_code.value}' is locked until the previous level's exam is passed"
            )
        return list(await self._repo.list_modules_by_level_code(level_code))

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
        return lesson
