from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.learning_profile import CEFRLevel
from app.models.lesson import Lesson
from app.models.level import Level
from app.models.module import Module
from app.repositories.course_repository import CourseRepository


class CourseService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CourseRepository(session)

    async def list_levels(self) -> list[Level]:
        return list(await self._repo.list_levels())

    async def list_modules(self, level_code: CEFRLevel) -> list[Module]:
        return list(await self._repo.list_modules_by_level_code(level_code))

    async def list_lessons(self, module_slug: str) -> list[Lesson]:
        return list(await self._repo.list_lessons_by_module_slug(module_slug))

    async def get_lesson(self, lesson_slug: str) -> Lesson:
        lesson = await self._repo.get_lesson_by_slug(lesson_slug)
        if lesson is None:
            raise NotFoundError(f"Lesson '{lesson_slug}' not found")
        return lesson
