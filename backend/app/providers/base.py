from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from app.models.core import Capability, ModelResponse, ProviderCapabilities

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate_text(self, *, model: str, messages: list[dict[str, str]], max_output_tokens: int = 4000, **kwargs: Any) -> ModelResponse:
        raise NotImplementedError

    async def generate_structured(self, *, model: str, messages: list[dict[str, str]], output_model: type[T], max_output_tokens: int = 4000, **kwargs: Any) -> ModelResponse:
        response = await self.generate_text(model=model, messages=messages, max_output_tokens=max_output_tokens, **kwargs)
        if response.structured is None:
            response.structured = output_model.model_validate_json(response.text)
        elif not isinstance(response.structured, output_model):
            response.structured = output_model.model_validate(response.structured)
        return response

    @abstractmethod
    def get_capabilities(self, model: str) -> ProviderCapabilities:
        raise NotImplementedError

    def supports(self, model: str, capability: Capability) -> bool:
        return bool(getattr(self.get_capabilities(model), capability.value, False))
