import re
from dataclasses import dataclass

from app.core.exceptions import AIResponseParsingError
from app.integrations.ai.prompt_loader import load_prompt
from app.integrations.ai.provider import AIMessage, AIProvider

_WRITING_FEEDBACK_HEADERS = ("Good", "Grammar", "Vocabulary", "Natural version", "Try again")

# Tolerates markdown bold (`**Grammar:**`) and stray whitespace around a header
# line, since a 9B local model doesn't always follow "no markdown" perfectly.
_SECTION_HEADER_PATTERN = re.compile(
    r"^\**\s*(" + "|".join(re.escape(h) for h in _WRITING_FEEDBACK_HEADERS) + r")\s*:\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class WritingFeedback:
    good: str
    grammar: str
    vocabulary: str
    natural_version: str
    try_again: str


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
        return _parse_writing_feedback(raw)


def _parse_writing_feedback(raw: str) -> WritingFeedback:
    matches = list(_SECTION_HEADER_PATTERN.finditer(raw))

    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        canonical = next(
            h for h in _WRITING_FEEDBACK_HEADERS if h.lower() == match.group(1).lower()
        )
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        sections[canonical] = raw[start:end].strip()

    missing = [h for h in _WRITING_FEEDBACK_HEADERS if not sections.get(h)]
    if missing:
        raise AIResponseParsingError(
            f"AI response missing section(s) {missing}; got: {raw[:300]!r}"
        )

    return WritingFeedback(
        good=sections["Good"],
        grammar=sections["Grammar"],
        vocabulary=sections["Vocabulary"],
        natural_version=sections["Natural version"],
        try_again=sections["Try again"],
    )
