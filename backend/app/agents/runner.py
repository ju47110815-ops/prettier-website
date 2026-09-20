from __future__ import annotations

import time
from typing import Any

from app.agents.registry import AgentRegistry
from app.db.database import Database
from app.models.core import AgentDefinition, ModelTier
from app.providers.base import LLMProvider
from app.providers.router import ModelRouter
from app.services.budget import BudgetManager
from app.services.cost import CostCalculator


class AgentRunner:
    def __init__(self, providers: dict[str, LLMProvider], router: ModelRouter, database: Database, registry: AgentRegistry | None = None, cost_calculator: CostCalculator | None = None):
        self.providers, self.router, self.database = providers, router, database
        self.registry = registry or AgentRegistry()
        self.cost_calculator = cost_calculator or CostCalculator()

    async def run(self, *, job_id: str, phase: str, agent_id: str, profile: str, budget: BudgetManager, context: dict[str, Any], output_model: type[Any] | None = None) -> Any:
        definition = self.registry.get(agent_id)
        candidate = self.router.route(profile, definition.preferred_model_tier, definition.required_capabilities)
        provider = self.providers[candidate.provider]
        messages = [{"role": "system", "content": definition.instructions}, {"role": "user", "content": str(context)}]
        budget.check()
        started = time.perf_counter()
        response = await (provider.generate_structured(model=candidate.model, messages=messages, output_model=output_model, max_output_tokens=definition.max_output_tokens) if output_model else provider.generate_text(model=candidate.model, messages=messages, max_output_tokens=definition.max_output_tokens))
        response.usage.latency_ms = int((time.perf_counter() - started) * 1000)
        record = self.cost_calculator.record(job_id=job_id, agent_id=agent_id, phase=phase, provider=candidate.provider, model=candidate.model, tier=candidate.tier, usage=response.usage)
        budget.add(record.estimated_cost_usd)
        self.database.add_usage(record)
        return response.structured if output_model else response.text
