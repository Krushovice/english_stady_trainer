from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class AIMessage:
    role: Role
    content: str


class AIProvider(Protocol):
    """Chat-completion abstraction every AI feature (`app/services/ai_service.py`,
    once it exists) is built on, so the underlying model/vendor can change without
    touching feature code.

    Implementations return only the model's final answer. Reasoning/thinking
    models (e.g. Qwen3.5) emit a separate chain-of-thought alongside the real
    answer — that's consumed internally and discarded, so callers never need to
    know whether the underlying model reasons or not.
    """

    async def complete(self, messages: list[AIMessage], *, max_tokens: int) -> str: ...
