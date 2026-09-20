import pytest

from app.models.core import AgentUsage, ModelTier
from app.providers.mock_provider import MockProvider
from app.providers.router import ModelRouter
from app.services.budget import BudgetExceeded, BudgetManager
from app.services.cost import CostCalculator


def test_router_profile_and_cost():
    provider = MockProvider()
    candidate = ModelRouter({"mock": provider}).route("cheap-deepseek", ModelTier.CHEAP)
    assert candidate.provider == "mock"
    cost = CostCalculator().calculate("mock", "mock-model", AgentUsage(input_tokens=1000, output_tokens=500))
    assert cost == 0


def test_budget_stops_calls():
    budget = BudgetManager(1.0)
    budget.add(1.0)
    with pytest.raises(BudgetExceeded):
        budget.check()
