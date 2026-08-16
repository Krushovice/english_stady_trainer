from pathlib import Path

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.models.lesson_block import BlockType
from app.repositories.course_repository import CourseRepository
from app.schemas.content import GrammarTopicItem, LessonFile, VocabularyItem


class ContentLoaderService:
    """Syncs course content authored as YAML under `content/` into the database.

    Upserts by natural key (level code, module slug, lesson slug, vocabulary
    headword, grammar topic slug), so re-running the loader after editing a
    file updates existing rows instead of duplicating them. Adding a lesson
    is a content change; it never requires touching this code.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CourseRepository(session)

    async def sync_directory(self, content_dir: Path) -> list[Lesson]:
        lessons = [await self.sync_file(path) for path in sorted(content_dir.rglob("*.yaml"))]
        await self._session.commit()
        return lessons

    async def sync_file(self, path: Path) -> Lesson:
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

        return lesson
