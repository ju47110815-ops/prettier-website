from __future__ import annotations

import os
from typing import Any

from app.models.core import ModelResponse, ProviderCapabilities
from app.providers.base import LLMProvider


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")

    async def generate_text(self, *, model: str, messages: list[dict[str, str]], max_output_tokens: int = 4000, **kwargs: Any) -> ModelResponse:
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured")
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
        response = await client.chat.completions.create(model=model, messages=messages, max_tokens=max_output_tokens, **kwargs)
        usage = response.usage
        from app.models.core import AgentUsage
        return ModelResponse(provider=self.name, model=model, text=response.choices[0].message.content or "", usage=AgentUsage(input_tokens=usage.prompt_tokens if usage else 0, output_tokens=usage.completion_tokens if usage else 0), finish_reason=response.choices[0].finish_reason)

    def get_capabilities(self, model: str) -> ProviderCapabilities:
        return ProviderCapabilities(structured_output=True, json_output=True, tool_calling=True, context_size=64000, max_output=8192)
