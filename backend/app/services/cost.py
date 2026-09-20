from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.models.core import AgentUsage, UsageRecord


class CostCalculator:
    def __init__(self, pricing_path: str | Path = "config/pricing.yaml"):
        with Path(pricing_path).open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        self.prices: dict[str, dict[str, float]] = data.get("models", {})

    def calculate(self, provider: str, model: str, usage: AgentUsage) -> float:
        price = self.prices.get(f"{provider}/{model}", {})
        billable_input = max(usage.input_tokens - usage.cached_input_tokens, 0)
        return (billable_input * price.get("input", 0) + usage.cached_input_tokens * price.get("cached_input", price.get("input", 0)) + usage.output_tokens * price.get("output", 0)) / 1_000_000

    def record(self, *, job_id: str, agent_id: str, phase: str, provider: str, model: str, tier: Any, usage: AgentUsage, retries: int = 0) -> UsageRecord:
        return UsageRecord(job_id=job_id, agent_id=agent_id, phase=phase, provider=provider, model=model, model_tier=tier, input_tokens=usage.input_tokens, cached_input_tokens=usage.cached_input_tokens, output_tokens=usage.output_tokens, reasoning_tokens=usage.reasoning_tokens, latency_ms=usage.latency_ms, retries=retries, estimated_cost_usd=self.calculate(provider, model, usage))
