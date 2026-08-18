import pytest

from app.core.exceptions import AIResponseParsingError
from app.integrations.ai.mock_provider import MockAIProvider
from app.models.learning_profile import CEFRLevel
from app.services.ai_service import (
    _WRITING_FEEDBACK_HEADERS,
    AIService,
    HomeworkTask,
    WritingFeedback,
    _parse_labeled_sections,
)

_WELL_FORMED_RESPONSE = """
Good:
Ты чётко объяснил свою мысль.

Grammar:
Ошибка: "she don't" вместо "she doesn't" — подлежащее третьего лица единственного числа.

Vocabulary:
Вместо "very good" попробуй "great" или "excellent".

Natural version:
She doesn't like coffee, but she loves tea.

Try again:
Напиши 2 предложения о том, что не любит твой друг, используя "doesn't".
"""

_WELL_FORMED_HOMEWORK_RESPONSE = """
Task 1:
Напиши предложение о том, что ты делал вчера, используя слово "commute".

Task 2:
Опиши свой обычный рабочий день, используя Present Simple.

Task 3:
Напиши, чем ты занимаешься по выходным, используя слово "usually".
"""


async def test_generate_writing_feedback_parses_provider_response():
    provider = MockAIProvider(response=_WELL_FORMED_RESPONSE)
    service = AIService(provider)

    feedback = await service.generate_writing_feedback("She don't like coffee.", max_tokens=1500)

    assert feedback == WritingFeedback(
        good="Ты чётко объяснил свою мысль.",
        grammar='Ошибка: "she don\'t" вместо "she doesn\'t" — подлежащее третьего лица '
        "единственного числа.",
        vocabulary='Вместо "very good" попробуй "great" или "excellent".',
        natural_version="She doesn't like coffee, but she loves tea.",
        try_again='Напиши 2 предложения о том, что не любит твой друг, используя "doesn\'t".',
    )


async def test_generate_writing_feedback_sends_system_prompt_and_user_text():
    provider = MockAIProvider(response=_WELL_FORMED_RESPONSE)
    service = AIService(provider)

    await service.generate_writing_feedback("She don't like coffee.", max_tokens=1500)

    [messages] = provider.received_calls
    assert messages[0].role == "system"
    assert "Good:" in messages[0].content
    assert messages[1].role == "user"
    assert messages[1].content == "She don't like coffee."


async def test_generate_homework_tasks_parses_provider_response():
    provider = MockAIProvider(response=_WELL_FORMED_HOMEWORK_RESPONSE)
    service = AIService(provider)

    tasks = await service.generate_homework_tasks(
        lesson_title="Daily routine",
        vocabulary=["commute", "usually"],
        grammar_topics=["Present Simple"],
        level=CEFRLevel.A2,
        max_tokens=1500,
    )

    assert tasks == [
        HomeworkTask(
            id="task-1",
            instruction='Напиши предложение о том, что ты делал вчера, используя слово "commute".',
        ),
        HomeworkTask(
            id="task-2", instruction="Опиши свой обычный рабочий день, используя Present Simple."
        ),
        HomeworkTask(
            id="task-3",
            instruction='Напиши, чем ты занимаешься по выходным, используя слово "usually".',
        ),
    ]


async def test_generate_homework_tasks_sends_system_prompt_and_lesson_context():
    provider = MockAIProvider(response=_WELL_FORMED_HOMEWORK_RESPONSE)
    service = AIService(provider)

    await service.generate_homework_tasks(
        lesson_title="Daily routine",
        vocabulary=["commute", "usually"],
        grammar_topics=["Present Simple"],
        level=CEFRLevel.A2,
        max_tokens=1500,
    )

    [messages] = provider.received_calls
    assert messages[0].role == "system"
    assert "Task 1:" in messages[0].content
    # Lesson specifics go in the user turn, not the system prompt — some chat
    # templates (this model's included) reject a request with no user message.
    assert messages[1].role == "user"
    assert "Daily routine" in messages[1].content
    assert "commute" in messages[1].content
    assert "Present Simple" in messages[1].content
    assert "A2" in messages[1].content


async def test_generate_homework_tasks_handles_missing_level_and_context():
    provider = MockAIProvider(response=_WELL_FORMED_HOMEWORK_RESPONSE)
    service = AIService(provider)

    tasks = await service.generate_homework_tasks(
        lesson_title="Daily routine",
        vocabulary=[],
        grammar_topics=[],
        level=None,
        max_tokens=1500,
    )

    assert len(tasks) == 3


def test_parse_labeled_sections_tolerates_markdown_bold_headers():
    raw = (
        "**Good:**\nNice try.\n\n"
        "**Grammar:**\nNo mistakes.\n\n"
        "**Vocabulary:**\nFine as is.\n\n"
        "**Natural version:**\nAll good.\n\n"
        "**Try again:**\nWrite one more sentence."
    )

    sections = _parse_labeled_sections(raw, _WRITING_FEEDBACK_HEADERS)

    assert sections["Good"] == "Nice try."
    assert sections["Try again"] == "Write one more sentence."


def test_parse_labeled_sections_is_case_insensitive_on_headers():
    raw = (
        "GOOD:\nfine\n\ngrammar:\nfine\n\nVOCABULARY:\nfine\n\n"
        "natural version:\nfine\n\nTRY AGAIN:\nfine"
    )

    sections = _parse_labeled_sections(raw, _WRITING_FEEDBACK_HEADERS)

    assert sections == {
        "Good": "fine",
        "Grammar": "fine",
        "Vocabulary": "fine",
        "Natural version": "fine",
        "Try again": "fine",
    }


def test_parse_labeled_sections_raises_on_missing_section():
    raw = "Good:\nNice.\n\nGrammar:\nFine.\n\nVocabulary:\nFine.\n\nNatural version:\nAll good."

    with pytest.raises(AIResponseParsingError):
        _parse_labeled_sections(raw, _WRITING_FEEDBACK_HEADERS)


def test_parse_labeled_sections_raises_on_unstructured_text():
    with pytest.raises(AIResponseParsingError):
        _parse_labeled_sections("Sorry, I can't help with that.", _WRITING_FEEDBACK_HEADERS)
