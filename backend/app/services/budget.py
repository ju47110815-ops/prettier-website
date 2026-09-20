from __future__ import annotations

from dataclasses import dataclass


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class BudgetManager:
    max_cost_usd: float
    current_cost_usd: float = 0.0
    warning_threshold: float = 0.8

    @property
    def remaining_usd(self) -> float:
        return max(self.max_cost_usd - self.current_cost_usd, 0.0)

    @property
    def percentage_consumed(self) -> float:
        return 0.0 if self.max_cost_usd <= 0 else self.current_cost_usd / self.max_cost_usd

    @property
    def exceeded(self) -> bool:
        return self.current_cost_usd >= self.max_cost_usd

    def can_start(self, estimated_cost_usd: float = 0.0) -> bool:
        return not self.exceeded and self.current_cost_usd + estimated_cost_usd <= self.max_cost_usd

    def check(self, estimated_cost_usd: float = 0.0) -> None:
        if not self.can_start(estimated_cost_usd):
            raise BudgetExceeded(f"Budget exceeded: ${self.current_cost_usd:.4f} of ${self.max_cost_usd:.4f} used")

    def add(self, cost_usd: float) -> None:
        self.current_cost_usd += max(cost_usd, 0.0)
