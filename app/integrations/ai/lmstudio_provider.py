from openai import APIConnectionError, APITimeoutError, AsyncOpenAI

from app.core.exceptions import AIProviderUnavailableError
from app.integrations.ai.provider import AIMessage


class LMStudioProvider:
    """Talks to a locally running LM Studio server over its OpenAI-compatible API.

    Works with any OpenAI-compatible endpoint (LM Studio, vLLM, a future cloud
    provider) — only the base URL/key/model change; the interface stays the same.
    """

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._model = model

    async def complete(self, messages: list[AIMessage], *, max_tokens: int) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                max_tokens=max_tokens,
            )
        except (APIConnectionError, APITimeoutError) as exc:
            raise AIProviderUnavailableError(
                f"AI provider at {self._client.base_url} is unreachable"
            ) from exc

        return response.choices[0].message.content or ""
