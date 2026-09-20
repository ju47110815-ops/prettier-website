from __future__ import annotations

import json
from typing import Any

from app.models.core import AgentUsage, ModelResponse, ProviderCapabilities
from app.providers.base import LLMProvider


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, response_factory: Any = None):
        self.calls: list[dict[str, Any]] = []
        self.response_factory = response_factory

    async def generate_text(self, *, model: str, messages: list[dict[str, str]], max_output_tokens: int = 4000, **kwargs: Any) -> ModelResponse:
        self.calls.append({"model": model, "messages": messages, "max_output_tokens": max_output_tokens, **kwargs})
        payload = self.response_factory(messages) if self.response_factory else {"summary": "Mock result", "items": []}
        text = payload if isinstance(payload, str) else json.dumps(payload)
        input_tokens = sum(len(message.get("content", "")) for message in messages) // 4
        return ModelResponse(provider=self.name, model=model, text=text, structured=payload if isinstance(payload, dict) else None, usage=AgentUsage(input_tokens=input_tokens, output_tokens=len(text) // 4))

    def get_capabilities(self, model: str) -> ProviderCapabilities:
        return ProviderCapabilities(structured_output=True, json_output=True, tool_calling=True, context_size=32000, max_output=8192)
