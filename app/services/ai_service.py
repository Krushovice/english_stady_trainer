import re
from dataclasses import dataclass

from app.core.exceptions import AIResponseParsingError
from app.integrations.ai.prompt_loader import load_prompt
from app.integrations.ai.provider import AIMessage, AIProvider
from app.models.learning_profile import CEFRLevel

_WRITING_FEEDBACK_HEADERS = ("Good", "Grammar", "Vocabulary", "Natural version", "Try again")
_HOMEWORK_TASK_HEADERS = ("Task 1", "Task 2", "Task 3")


@dataclass(frozen=True)
class WritingFeedback:
    good: str
    grammar: str
    vocabulary: str
    natural_version: str
    try_again: str


@dataclass(frozen=True)
class HomeworkTask:
    id: str
    instruction: str


class AIService:
    """Business-logic layer for AI features — owns prompts and response parsing.

    `AIProvider` only knows how to run a chat completion; this layer knows what
    to ask for and how to turn the answer into a typed result the API can return.
    """

    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    async def generate_writing_feedback(self, text: str, *, max_tokens: int) -> WritingFeedback:
        messages = [
            AIMessage(role="system", content=load_prompt("writing_feedback_v1")),
            AIMessage(role="user", content=text),
        ]
        raw = await self._provider.complete(messages, max_tokens=max_tokens)
        sections = _parse_labeled_sections(raw, _WRITING_FEEDBACK_HEADERS)
        return WritingFeedback(
            good=sections["Good"],
            grammar=sections["Grammar"],
            vocabulary=sections["Vocabulary"],
            natural_version=sections["Natural version"],
            try_again=sections["Try again"],
        )

    async def generate_homework_tasks(
        self,
        *,
        lesson_title: str,
        vocabulary: list[str],
        grammar_topics: list[str],
        level: CEFRLevel | None,
        max_tokens: int,
    ) -> list[HomeworkTask]:
        # The lesson's specifics go in the user turn, not the system prompt —
        # some chat templates (this model's included) reject a request with
        # no user message at all.
        vocabulary_text = ", ".join(vocabulary) if vocabulary else "(нет данных)"
        grammar_text = ", ".join(grammar_topics) if grammar_topics else "(нет данных)"
        user_message = (
            f"Learner level: {level.value if level is not None else 'не определён'}\n"
            f"Lesson: {lesson_title}\n"
            f"Vocabulary: {vocabulary_text}\n"
            f"Grammar topic(s): {grammar_text}\n\n"
            "Generate the homework now."
        )
        messages = [
            AIMessage(role="system", content=load_prompt("homework_generation_v1")),
            AIMessage(role="user", content=user_message),
        ]
        raw = await self._provider.complete(messages, max_tokens=max_tokens)
        sections = _parse_labeled_sections(raw, _HOMEWORK_TASK_HEADERS)
        return [
            HomeworkTask(id=f"task-{i}", instruction=sections[header])
            for i, header in enumerate(_HOMEWORK_TASK_HEADERS, start=1)
        ]


def _parse_labeled_sections(raw: str, headers: tuple[str, ...]) -> dict[str, str]:
    """Split `raw` into the given labeled sections (`"Header:\\n...text..."`).

    Tolerates markdown bold (`**Header:**`) and stray whitespace around a
    header line, since a 9B local model doesn't always follow "no markdown"
    perfectly. Raises `AIResponseParsingError` if any expected header/body is
    missing — the model didn't follow the requested format.
    """
    pattern = re.compile(
        r"^\**\s*(" + "|".join(re.escape(h) for h in headers) + r")\s*:\**\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    matches = list(pattern.finditer(raw))

    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        canonical = next(h for h in headers if h.lower() == match.group(1).lower())
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        sections[canonical] = raw[start:end].strip()

    missing = [h for h in headers if not sections.get(h)]
    if missing:
        raise AIResponseParsingError(
            f"AI response missing section(s) {missing}; got: {raw[:300]!r}"
        )

    return sections
