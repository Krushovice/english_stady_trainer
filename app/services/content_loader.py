import uuid
from pathlib import Path

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import ExerciseType
from app.models.lesson import Lesson
from app.models.lesson_block import BlockType
from app.repositories.course_repository import CourseRepository
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.content import (
    ExerciseContent,
    FinalExamBankFile,
    GrammarTopicItem,
    LessonFile,
    PlacementBankFile,
    VocabularyItem,
)

PLACEMENT_BANK_DIR_NAME = "placement_test"
FINAL_EXAM_BANK_DIR_NAME = "final_exam"


class ContentLoaderService:
    """Syncs course content authored as YAML under `content/` into the database.

    Upserts by natural key (level code, module slug, lesson slug, vocabulary
    headword, grammar topic slug, exercise slug), so re-running the loader
    after editing a file updates existing rows instead of duplicating them.
    Adding a lesson is a content change; it never requires touching this
    code. Exercises removed from a file are left in place rather than
    deleted, so editing a lesson never silently drops a learner's attempt
    history for an exercise that's still in the database.

    Files under a `placement_test/` directory are the placement-item bank —
    a flat list of exercises with no lesson (see `PlacementBankFile`) —
    rather than a lesson file, and are synced separately. Same for
    `final_exam/` (see `FinalExamBankFile`) — the course-wide final exam's
    own dedicated item pool.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CourseRepository(session)
        self._exercises = ExerciseRepository(session)

    async def sync_directory(self, content_dir: Path) -> list[Lesson]:
        # Two passes: metadata (level/module/lesson/vocabulary/grammar) for
        # every file first, then exercises for every file second. A single
        # pass in path-sorted order would make an exercise's
        # grammar_topic_slug/vocabulary_headword reference fail whenever it
        # points at a lesson that happens to sort later (e.g. a revision
        # lesson recycling grammar from lessons taught after it
        # alphabetically but before it pedagogically).
        lesson_files = []
        placement_files = []
        final_exam_files = []
        for path in sorted(content_dir.rglob("*.yaml")):
            if path.parent.name == PLACEMENT_BANK_DIR_NAME:
                placement_files.append(path)
            elif path.parent.name == FINAL_EXAM_BANK_DIR_NAME:
                final_exam_files.append(path)
            else:
                lesson_files.append(path)

        pending = [await self._sync_lesson_metadata(path) for path in lesson_files]
        lessons = []
        for lesson, data in pending:
            await self._sync_lesson_exercises(lesson, data)
            lessons.append(lesson)
        for path in placement_files:
            await self.sync_placement_bank_file(path)
        for path in final_exam_files:
            await self.sync_final_exam_bank_file(path)

        await self._session.commit()
        return lessons

    async def sync_file(self, path: Path) -> Lesson:
        """Sync a single lesson file end to end (metadata + exercises).

        Convenience wrapper for scripts/tests syncing one known-self-contained
        file; `sync_directory` uses the split two-pass path instead so
        cross-file grammar/vocabulary references resolve regardless of
        alphabetical file order.
        """
        lesson, data = await self._sync_lesson_metadata(path)
        await self._sync_lesson_exercises(lesson, data)
        return lesson

    async def _sync_lesson_metadata(self, path: Path) -> tuple[Lesson, LessonFile]:
        raw = yaml.safe_load(path.read_text())
        data = LessonFile.model_validate(raw)

        level = await self._repo.upsert_level(
            code=data.level.code, order_index=data.level.order_index
        )
        module = await self._repo.upsert_module(
            level_id=level.id,
            slug=data.module.slug,
            title=data.module.title,
            order_index=data.module.order_index,
        )
        lesson = await self._repo.upsert_lesson(
            module_id=module.id,
            slug=data.lesson.slug,
            title=data.lesson.title,
            order_index=data.lesson.order_index,
            content_path=str(path),
        )

        await self._repo.replace_blocks(
            lesson.id, [(block.type, block.order_index, block.content) for block in data.blocks]
        )

        vocabulary_items = [
            VocabularyItem.model_validate(item)
            for block in data.blocks
            if block.type == BlockType.VOCABULARY
            for item in block.content.get("items", [])
        ]
        grammar_items = [
            GrammarTopicItem.model_validate(topic)
            for block in data.blocks
            if block.type == BlockType.GRAMMAR
            for topic in block.content.get("topics", [])
        ]

        vocab_rows = [
            await self._repo.upsert_vocabulary(**item.model_dump()) for item in vocabulary_items
        ]
        grammar_rows = [
            await self._repo.upsert_grammar_topic(**topic.model_dump()) for topic in grammar_items
        ]

        await self._repo.set_lesson_vocabulary(lesson.id, [v.id for v in vocab_rows])
        await self._repo.set_lesson_grammar_topics(lesson.id, [g.id for g in grammar_rows])

        return lesson, data

    async def _sync_lesson_exercises(self, lesson: Lesson, data: LessonFile) -> None:
        exercise_items = [
            ExerciseContent.model_validate(item)
            for block in data.blocks
            if block.type == BlockType.EXERCISES
            for item in block.content.get("items", [])
        ]
        for item in exercise_items:
            await self._upsert_exercise(item, lesson_id=lesson.id, is_placement_item=False)

        # Mini-test items belong to (and are authored alongside) the lesson
        # whose material they test — they're surfaced later, on the *next*
        # lesson's page, as "quick review of the previous topic". See
        # app/services/exercise_service.py's get_mini_test_for_lesson.
        mini_test_items = [
            ExerciseContent.model_validate(item)
            for block in data.blocks
            if block.type == BlockType.MINI_TEST
            for item in block.content.get("items", [])
        ]
        for item in mini_test_items:
            await self._upsert_exercise(
                item, lesson_id=lesson.id, is_placement_item=False, is_mini_test_item=True
            )

    async def sync_placement_bank_file(self, path: Path) -> None:
        raw = yaml.safe_load(path.read_text())
        data = PlacementBankFile.model_validate(raw)
        for item in data.items:
            await self._upsert_exercise(item, lesson_id=None, is_placement_item=True)

    async def sync_final_exam_bank_file(self, path: Path) -> None:
        raw = yaml.safe_load(path.read_text())
        data = FinalExamBankFile.model_validate(raw)
        for item in data.items:
            await self._upsert_exercise(
                item, lesson_id=None, is_placement_item=False, is_final_exam_item=True
            )

    async def _upsert_exercise(
        self,
        item: ExerciseContent,
        *,
        lesson_id: uuid.UUID | None,
        is_placement_item: bool,
        is_mini_test_item: bool = False,
        is_final_exam_item: bool = False,
    ) -> None:
        grammar_topic_id = None
        if item.grammar_topic_slug is not None:
            topic = await self._repo.get_grammar_topic_by_slug(item.grammar_topic_slug)
            if topic is None:
                raise ValueError(
                    f"Exercise '{item.slug}' references unknown grammar topic "
                    f"'{item.grammar_topic_slug}'"
                )
            grammar_topic_id = topic.id

        vocabulary_id = None
        if item.vocabulary_headword is not None:
            vocabulary = await self._repo.get_vocabulary_by_headword(item.vocabulary_headword)
            if vocabulary is None:
                raise ValueError(
                    f"Exercise '{item.slug}' references unknown vocabulary "
                    f"'{item.vocabulary_headword}'"
                )
            vocabulary_id = vocabulary.id

        await self._exercises.upsert_exercise(
            slug=item.slug,
            lesson_id=lesson_id,
            exercise_type=ExerciseType(item.type),
            skill=item.skill,
            difficulty=item.difficulty,
            prompt=item.prompt,
            answer_key=item.answer_key,
            explanation=item.explanation,
            grammar_topic_id=grammar_topic_id,
            vocabulary_id=vocabulary_id,
            is_placement_item=is_placement_item,
            is_mini_test_item=is_mini_test_item,
            is_final_exam_item=is_final_exam_item,
        )
