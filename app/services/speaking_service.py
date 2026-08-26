import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.exceptions import (
    EmptyTranscriptError,
    NotFoundError,
    SpeakingAttemptAlreadySubmittedError,
)
from app.integrations.ai.provider import AIProvider
from app.integrations.stt.provider import STTProvider
from app.models.lesson_block import BlockType
from app.models.speaking import SpeakingAttempt
from app.repositories.course_repository import CourseRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.learning_profile_repository import LearningProfileRepository
from app.repositories.speaking_repository import SpeakingRepository
from app.services.ai_service import AIService


class SpeakingService:
    """Generates a speaking prompt from the user's most recently studied
    lesson, then transcribes and grades a spoken answer to it — CLAUDE.md's
    "prompt -> user speaks -> STT -> evaluation -> feedback -> retry" flow.

    Two-step generate-then-submit shape, same as `HomeworkService`. Retry is
    a new `generate_prompt` call, not resubmitting audio to the same attempt.
    Ownership checks (404, not 403) match the pattern used across
    Homework/Conversation/Review.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._exercises = ExerciseRepository(session)
        self._course = CourseRepository(session)
        self._profiles = LearningProfileRepository(session)
        self._speaking = SpeakingRepository(session)

    async def generate_prompt(
        self, user_id: uuid.UUID, ai_provider: AIProvider, *, max_tokens: int
    ) -> SpeakingAttempt:
        lesson_id = await self._exercises.get_most_recently_studied_lesson_id(user_id)
        if lesson_id is None:
            raise NotFoundError("No recently studied lesson found — complete some exercises first.")

        lesson = await self._course.get_lesson_by_id(lesson_id)
        if lesson is None:  # pragma: no cover - FK guarantees this, defensive only
            raise NotFoundError(f"Lesson '{lesson_id}' not found")

        profile = await self._profiles.get_by_user_id(user_id)
        level = profile.level_speaking if profile is not None else None

        prompt_text = await AIService(ai_provider).generate_speaking_prompt(
            lesson_title=lesson.title,
            vocabulary=[v.headword for v in lesson.vocabulary],
            grammar_topics=[t.title for t in lesson.grammar_topics],
            level=level,
            max_tokens=max_tokens,
        )

        attempt = SpeakingAttempt(user_id=user_id, lesson_id=lesson.id, prompt=prompt_text)
        self._speaking.add(attempt)
        await self._session.commit()
        # See HomeworkService.generate() for why: commit() expires the object,
        # and this scalar relationship is provably `lesson` already.
        set_committed_value(attempt, "lesson", lesson)
        return attempt

    async def start_lesson_attempt(self, user_id: uuid.UUID, lesson_slug: str) -> SpeakingAttempt:
        """Starts a Speaking attempt from a lesson's own authored `speaking`
        block prompt, instead of an AI-generated one — the lesson already
        wrote the exact task (topic, vocabulary to use), so there's nothing
        for the AI to add at this step. Evaluation (`submit_attempt`) still
        goes through STT + AI feedback as normal.
        """
        lesson = await self._course.get_lesson_by_slug(lesson_slug)
        if lesson is None:
            raise NotFoundError(f"Lesson '{lesson_slug}' not found")

        speaking_block = next(
            (block for block in lesson.blocks if block.block_type == BlockType.SPEAKING), None
        )
        if speaking_block is None:
            raise NotFoundError(f"Lesson '{lesson_slug}' has no speaking task")

        prompt_text = speaking_block.content.get("prompt", "")
        attempt = SpeakingAttempt(user_id=user_id, lesson_id=lesson.id, prompt=prompt_text)
        self._speaking.add(attempt)
        await self._session.commit()
        set_committed_value(attempt, "lesson", lesson)
        return attempt

    async def submit_attempt(
        self,
        user_id: uuid.UUID,
        attempt_id: uuid.UUID,
        audio: bytes,
        filename: str,
        stt_provider: STTProvider,
        ai_provider: AIProvider,
        *,
        max_tokens: int,
    ) -> SpeakingAttempt:
        attempt = await self._get_owned(user_id, attempt_id)
        if attempt.submitted_at is not None:
            raise SpeakingAttemptAlreadySubmittedError(
                f"Speaking attempt '{attempt_id}' already has a submitted answer"
            )
        # Already eager-loaded by the repository; capture it now since commit()
        # below expires it and a post-commit access would try (and fail) to
        # lazy-load it synchronously.
        lesson = attempt.lesson

        transcript = await stt_provider.transcribe(audio, filename, language="en")
        if not transcript.strip():
            raise EmptyTranscriptError("Couldn't detect any speech in the recording.")

        feedback = await AIService(ai_provider).generate_speaking_feedback(
            attempt.prompt, transcript, max_tokens=max_tokens
        )

        attempt.transcript = transcript
        attempt.feedback = {
            "good": feedback.good,
            "grammar": feedback.grammar,
            "vocabulary": feedback.vocabulary,
            "natural_version": feedback.natural_version,
            "try_again": feedback.try_again,
        }
        attempt.submitted_at = datetime.now(UTC)
        await self._session.commit()
        set_committed_value(attempt, "lesson", lesson)
        return attempt

    async def get(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> SpeakingAttempt:
        return await self._get_owned(user_id, attempt_id)

    async def _get_owned(self, user_id: uuid.UUID, attempt_id: uuid.UUID) -> SpeakingAttempt:
        attempt = await self._speaking.get_by_id(attempt_id)
        if attempt is None or attempt.user_id != user_id:
            raise NotFoundError(f"Speaking attempt '{attempt_id}' not found")
        return attempt
