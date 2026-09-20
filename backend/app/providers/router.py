from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from app.models.core import Capability, ModelTier
from app.providers.base import LLMProvider


@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str
    tier: ModelTier


class ModelRouter:
    def __init__(self, providers: dict[str, LLMProvider], config_path: str | Path = "config/routing-profiles.yaml"):
        self.providers = providers
        with Path(config_path).open(encoding="utf-8") as handle:
            self.profiles = yaml.safe_load(handle).get("profiles", {})

    def candidates(self, profile: str, tier: ModelTier) -> Iterable[ModelCandidate]:
        configured = self.profiles.get(profile, {}).get(tier.value, [])
        for value in configured:
            provider, model = value.split("/", 1)
            if provider in self.providers:
                yield ModelCandidate(provider, model, tier)

    def route(self, profile: str, tier: ModelTier, required_capabilities: list[Capability] | None = None) -> ModelCandidate:
        required_capabilities = required_capabilities or []
        for candidate in self.candidates(profile, tier):
            provider = self.providers[candidate.provider]
            if all(provider.supports(candidate.model, capability) for capability in required_capabilities):
                return candidate
        raise LookupError(f"No model in profile '{profile}' supports tier '{tier.value}' and capabilities {required_capabilities}")
