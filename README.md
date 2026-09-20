# Website Migration Engine

Local MVP backend for provider-agnostic migration of small public websites (roughly 5-100 pages). Python owns the pipeline, state transitions, budgets, validation, and bounded QA; providers only implement normalized model inference.

## Architecture

- `AgentDefinition`, `AgentRegistry`, and `AgentRunner` provide stable application-level agent contracts.
- `ModelRouter` uses external routing profiles and capability checks. `MockProvider` supports local tests; OpenAI and DeepSeek adapters keep provider SDK details isolated.
- `CostCalculator` loads `config/pricing.yaml`. Every model call creates a persisted `UsageRecord`; `BudgetManager` blocks calls after the job budget is exhausted.
- `BoundedCrawler` creates one same-domain crawl snapshot before research and enforces page, depth, byte, timeout, and asset bounds.
- SQLite persists jobs, usage, and artifacts. Each job receives an isolated `workspaces/<job-id>/` directory.
- Research agents run in parallel, architecture agents run in parallel, implementation agents run sequentially, and deterministic validation precedes bounded QA.

The 15 placeholder agents live in `backend/app/agents/registry.py`. Detailed definitions can be supplied later without changing pipeline code.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
$env:PYTHONPATH = "backend"
```

Copy `.env.example` to `.env` and configure the database, workspace root, budgets, crawl limits, and optional provider keys.

## Run

```powershell
$env:PYTHONPATH="backend"
uvicorn app.main:app --reload
python -m app.cli migrate --url https://example.org --prompt "Improve mobile usability" --profile cheap-deepseek --max-cost 3
python -m app.cli job <job-id>
python -m app.cli compare <job-id-a> <job-id-b>
```

The API provides job creation/list/detail, SSE-style events, usage, metrics, evaluation, report, blocker, approval, and cancellation endpoints.

Set `OPENAI_API_KEY` or `DEEPSEEK_API_KEY` to enable the corresponding adapter. Model IDs and prices belong in `config/models.yaml` and `config/pricing.yaml`, not orchestration code.

## Tests

```powershell
$env:PYTHONPATH="backend"
python -m pytest -q
```

Tests use `MockProvider` and do not consume API credits. The current suite covers routing, cost and budgets, bounded same-domain crawling, workspace traversal, and a fake end-to-end migration with evaluation artifacts.

## Limitations

This internal MVP does not include authentication, billing, deployment, Docker sandboxing, durable queues, browser/Lighthouse tooling, advanced comparisons, or production-grade approval persistence. Generated implementation is intentionally placeholder-driven until the detailed agent definitions are supplied. Sensitive facts, legal text, image rights, and current personal data require human review.