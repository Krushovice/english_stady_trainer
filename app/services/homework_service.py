import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.exceptions import NotFoundError
from app.integrations.ai.provider import AIProvider
from app.models.homework import Homework, HomeworkAttempt
from app.repositories.course_repository import CourseRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.homework_repository import HomeworkRepository
from app.repositories.learning_profile_repository import LearningProfileRepository
from app.services.ai_service import AIService


class HomeworkService:
    """Generates and grades homework from the user's most recently studied lesson.

    `get`/`submit_task`'s ownership check (404, not 403, on a mismatched
    `user_id`) matches the pattern already used for review items — don't
    reveal whether a homework id exists for someone else.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._exercises = ExerciseRepository(session)
        self._course = CourseRepository(session)
        self._profiles = LearningProfileRepository(session)
        self._homework = HomeworkRepository(session)

    async def generate(
        self, user_id: uuid.UUID, ai_provider: AIProvider, *, max_tokens: int
    ) -> Homework:
        lesson_id = await self._exercises.get_most_recently_studied_lesson_id(user_id)
        if lesson_id is None:
            raise NotFoundError("No recently studied lesson found — complete some exercises first.")

        lesson = await self._course.get_lesson_by_id(lesson_id)
        if lesson is None:  # pragma: no cover - FK guarantees this, defensive only
            raise NotFoundError(f"Lesson '{lesson_id}' not found")

        profile = await self._profiles.get_by_user_id(user_id)
        level = profile.level_writing if profile is not None else None

        tasks = await AIService(ai_provider).generate_homework_tasks(
            lesson_title=lesson.title,
            vocabulary=[v.headword for v in lesson.vocabulary],
            grammar_topics=[t.title for t in lesson.grammar_topics],
            level=level,
            max_tokens=max_tokens,
        )

        homework = Homework(
            user_id=user_id,
            lesson_id=lesson.id,
            tasks=[{"id": task.id, "instruction": task.instruction} for task in tasks],
        )
        self._homework.add(homework)
        await self._session.commit()
        # Plain attribute assignment on a relationship still triggers a lazy
        # *read* of the old value first (to diff for cascade bookkeeping) —
        # which an AsyncSession can't do outside an awaited call. A freshly
        # generated homework provably has these values, so set them as
        # already-loaded instead of letting the API layer's attribute access
        # (or this assignment itself) trigger that lazy load.
        set_committed_value(homework, "lesson", lesson)
        set_committed_value(homework, "attempts", [])
        return homework

    async def submit_task(
        self,
        user_id: uuid.UUID,
        homework_id: uuid.UUID,
        task_id: str,
        text: str,
        ai_provider: AIProvider,
        *,
        max_tokens: int,
    ) -> HomeworkAttempt:
        homework = await self._get_owned(user_id, homework_id)
        if not any(task["id"] == task_id for task in homework.tasks):
            raise NotFoundError(f"Task '{task_id}' not found in homework '{homework_id}'")

        feedback = await AIService(ai_provider).generate_writing_feedback(
            text, max_tokens=max_tokens
        )

        attempt = HomeworkAttempt(
            homework_id=homework.id,
            task_id=task_id,
            submitted_text=text,
            feedback={
                "good": feedback.good,
                "grammar": feedback.grammar,
                "vocabulary": feedback.vocabulary,
                "natural_version": feedback.natural_version,
                "try_again": feedback.try_again,
            },
        )
        self._homework.add_attempt(attempt)
        await self._session.commit()
        return attempt

    async def get(self, user_id: uuid.UUID, homework_id: uuid.UUID) -> Homework:
        return await self._get_owned(user_id, homework_id)

    async def _get_owned(self, user_id: uuid.UUID, homework_id: uuid.UUID) -> Homework:
        homework = await self._homework.get_by_id(homework_id)
        if homework is None or homework.user_id != user_id:
            raise NotFoundError(f"Homework '{homework_id}' not found")
        return homework
