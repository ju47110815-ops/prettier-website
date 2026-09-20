from __future__ import annotations

import os

from fastapi import FastAPI

from app.agents.runner import AgentRunner
from app.db.database import Database
from app.api.approvals import router as approvals_router
from app.api.events import router as events_router
from app.api.jobs import router as jobs_router
from app.pipeline.orchestrator import MigrationOrchestrator
from app.providers.mock_provider import MockProvider
from app.providers.router import ModelRouter
from app.services.workspace import WorkspaceService


def build_services():
    database = Database(os.getenv("DATABASE_PATH", "./workspaces/migration.db"))
    providers = {"mock": MockProvider()}
    if os.getenv("OPENAI_API_KEY"): 
        from app.providers.openai_provider import OpenAIProvider
        providers["openai"] = OpenAIProvider()
    if os.getenv("DEEPSEEK_API_KEY"):
        from app.providers.deepseek_provider import DeepSeekProvider
        providers["deepseek"] = DeepSeekProvider()
    router = ModelRouter(providers)
    runner = AgentRunner(providers, router, database)
    workspace = WorkspaceService(os.getenv("WORKSPACE_ROOT", "./workspaces"))
    return database, MigrationOrchestrator(database, runner, workspace)


database, orchestrator = build_services()
tasks = {}
app = FastAPI(title="Website Migration Engine", version="0.1.0")
app.include_router(jobs_router)
app.include_router(events_router)
app.include_router(approvals_router)

@app.get("/health")
def health():
    return {"status": "ok"}
