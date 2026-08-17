import pytest

from app.core.exceptions import AIResponseParsingError
from app.integrations.ai.mock_provider import MockAIProvider
from app.services.ai_service import AIService, WritingFeedback, _parse_writing_feedback

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


def test_parse_writing_feedback_tolerates_markdown_bold_headers():
    raw = (
        "**Good:**\nNice try.\n\n"
        "**Grammar:**\nNo mistakes.\n\n"
        "**Vocabulary:**\nFine as is.\n\n"
        "**Natural version:**\nAll good.\n\n"
        "**Try again:**\nWrite one more sentence."
    )

    feedback = _parse_writing_feedback(raw)

    assert feedback.good == "Nice try."
    assert feedback.try_again == "Write one more sentence."


def test_parse_writing_feedback_is_case_insensitive_on_headers():
    raw = (
        "GOOD:\nfine\n\ngrammar:\nfine\n\nVOCABULARY:\nfine\n\n"
        "natural version:\nfine\n\nTRY AGAIN:\nfine"
    )

    feedback = _parse_writing_feedback(raw)

    assert feedback == WritingFeedback(
        good="fine", grammar="fine", vocabulary="fine", natural_version="fine", try_again="fine"
    )


def test_parse_writing_feedback_raises_on_missing_section():
    raw = "Good:\nNice.\n\nGrammar:\nFine.\n\nVocabulary:\nFine.\n\nNatural version:\nAll good."

    with pytest.raises(AIResponseParsingError):
        _parse_writing_feedback(raw)


def test_parse_writing_feedback_raises_on_unstructured_text():
    with pytest.raises(AIResponseParsingError):
        _parse_writing_feedback("Sorry, I can't help with that.")
