import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.associations import lesson_grammar_topics, lesson_vocabulary
from app.models.grammar_topic import GrammarTopic
from app.models.learning_profile import CEFRLevel
from app.models.lesson import Lesson
from app.models.lesson_block import BlockType, LessonBlock
from app.models.level import Level
from app.models.module import Module
from app.models.vocabulary import Vocabulary


class CourseRepository:
    """Data access for the course tree (Level/Module/Lesson/LessonBlock) plus

    Vocabulary/GrammarTopic — bundled here because they're only ever written
    by the content loader and read together with a lesson.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- writes, used by the content loader ---

    async def upsert_level(self, code: CEFRLevel, order_index: int) -> Level:
        level = (
            await self._session.execute(select(Level).where(Level.code == code))
        ).scalar_one_or_none()
        if level is None:
            level = Level(code=code, order_index=order_index)
            self._session.add(level)
        else:
            level.order_index = order_index
        await self._session.flush()
        return level

    async def upsert_module(
        self, level_id: uuid.UUID, slug: str, title: str, order_index: int
    ) -> Module:
        module = (
            await self._session.execute(select(Module).where(Module.slug == slug))
        ).scalar_one_or_none()
        if module is None:
            module = Module(level_id=level_id, slug=slug, title=title, order_index=order_index)
            self._session.add(module)
        else:
            module.level_id = level_id
            module.title = title
            module.order_index = order_index
        await self._session.flush()
        return module

    async def upsert_lesson(
        self, module_id: uuid.UUID, slug: str, title: str, order_index: int, content_path: str
    ) -> Lesson:
        lesson = (
            await self._session.execute(select(Lesson).where(Lesson.slug == slug))
        ).scalar_one_or_none()
        if lesson is None:
            lesson = Lesson(
                module_id=module_id,
                slug=slug,
                title=title,
                order_index=order_index,
                content_path=content_path,
            )
            self._session.add(lesson)
        else:
            lesson.module_id = module_id
            lesson.title = title
            lesson.order_index = order_index
            lesson.content_path = content_path
        await self._session.flush()
        return lesson

    async def replace_blocks(
        self, lesson_id: uuid.UUID, blocks: Sequence[tuple[BlockType, int, dict]]
    ) -> None:
        await self._session.execute(delete(LessonBlock).where(LessonBlock.lesson_id == lesson_id))
        for block_type, order_index, content in blocks:
            self._session.add(
                LessonBlock(
                    lesson_id=lesson_id,
                    block_type=block_type,
                    order_index=order_index,
                    content=content,
                )
            )
        await self._session.flush()

    async def upsert_vocabulary(
        self, headword: str, translation: str, example_sentence: str, audio_url: str | None = None
    ) -> Vocabulary:
        vocab = (
            await self._session.execute(select(Vocabulary).where(Vocabulary.headword == headword))
        ).scalar_one_or_none()
        if vocab is None:
            vocab = Vocabulary(
                headword=headword,
                translation=translation,
                example_sentence=example_sentence,
                audio_url=audio_url,
            )
            self._session.add(vocab)
        else:
            vocab.translation = translation
            vocab.example_sentence = example_sentence
            vocab.audio_url = audio_url
        await self._session.flush()
        return vocab

    async def upsert_grammar_topic(self, slug: str, title: str, description: str) -> GrammarTopic:
        topic = (
            await self._session.execute(select(GrammarTopic).where(GrammarTopic.slug == slug))
        ).scalar_one_or_none()
        if topic is None:
            topic = GrammarTopic(slug=slug, title=title, description=description)
            self._session.add(topic)
        else:
            topic.title = title
            topic.description = description
        await self._session.flush()
        return topic

    async def set_lesson_vocabulary(
        self, lesson_id: uuid.UUID, vocabulary_ids: Sequence[uuid.UUID]
    ) -> None:
        await self._session.execute(
            delete(lesson_vocabulary).where(lesson_vocabulary.c.lesson_id == lesson_id)
        )
        for vocabulary_id in vocabulary_ids:
            await self._session.execute(
                lesson_vocabulary.insert().values(lesson_id=lesson_id, vocabulary_id=vocabulary_id)
            )
        await self._session.flush()

    async def set_lesson_grammar_topics(
        self, lesson_id: uuid.UUID, grammar_topic_ids: Sequence[uuid.UUID]
    ) -> None:
        await self._session.execute(
            delete(lesson_grammar_topics).where(lesson_grammar_topics.c.lesson_id == lesson_id)
        )
        for grammar_topic_id in grammar_topic_ids:
            await self._session.execute(
                lesson_grammar_topics.insert().values(
                    lesson_id=lesson_id, grammar_topic_id=grammar_topic_id
                )
            )
        await self._session.flush()

    # --- reads, used by the API ---

    async def list_levels(self) -> Sequence[Level]:
        result = await self._session.execute(select(Level).order_by(Level.order_index))
        return result.scalars().all()

    async def list_modules_by_level_code(self, code: CEFRLevel) -> Sequence[Module]:
        result = await self._session.execute(
            select(Module).join(Level).where(Level.code == code).order_by(Module.order_index)
        )
        return result.scalars().all()

    async def list_all_modules(self) -> Sequence[Module]:
        result = await self._session.execute(
            select(Module).options(selectinload(Module.level)).order_by(Module.order_index)
        )
        return result.scalars().all()

    async def list_lessons_by_module_slug(self, slug: str) -> Sequence[Lesson]:
        result = await self._session.execute(
            select(Lesson).join(Module).where(Module.slug == slug).order_by(Lesson.order_index)
        )
        return result.scalars().all()

    async def get_lesson_by_slug(self, slug: str) -> Lesson | None:
        result = await self._session.execute(
            select(Lesson)
            .where(Lesson.slug == slug)
            .options(
                selectinload(Lesson.blocks),
                selectinload(Lesson.vocabulary),
                selectinload(Lesson.grammar_topics),
            )
        )
        return result.scalar_one_or_none()

    async def get_lesson_by_id(self, lesson_id: uuid.UUID) -> Lesson | None:
        result = await self._session.execute(
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(selectinload(Lesson.vocabulary), selectinload(Lesson.grammar_topics))
        )
        return result.scalar_one_or_none()

    async def get_previous_lesson_in_level(self, lesson_id: uuid.UUID) -> Lesson | None:
        """The lesson immediately before this one, ordered by
        (module.order_index, lesson.order_index) within the same level.

        Backs the post-lesson mini-test: "quick review of the previous
        topic" only makes sense within one level's own sequence, not across
        a level boundary (a B1 lesson doesn't quiz A1 material).
        """
        current = (
            await self._session.execute(
                select(Lesson)
                .join(Module)
                .where(Lesson.id == lesson_id)
                .options(selectinload(Lesson.module))
            )
        ).scalar_one_or_none()
        if current is None:
            return None

        result = await self._session.execute(
            select(Lesson)
            .join(Module)
            .where(Module.level_id == current.module.level_id)
            .where(
                (Module.order_index < current.module.order_index)
                | (
                    (Module.order_index == current.module.order_index)
                    & (Lesson.order_index < current.order_index)
                )
            )
            .order_by(Module.order_index.desc(), Lesson.order_index.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_level_by_lesson_slug(self, slug: str) -> Level | None:
        result = await self._session.execute(
            select(Level).join(Module).join(Lesson).where(Lesson.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_vocabulary_by_headword(self, headword: str) -> Vocabulary | None:
        result = await self._session.execute(
            select(Vocabulary).where(Vocabulary.headword == headword)
        )
        return result.scalar_one_or_none()

    async def get_grammar_topic_by_slug(self, slug: str) -> GrammarTopic | None:
        result = await self._session.execute(select(GrammarTopic).where(GrammarTopic.slug == slug))
        return result.scalar_one_or_none()
