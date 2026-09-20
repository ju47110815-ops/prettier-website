import asyncio
from pathlib import Path

from app.agents.runner import AgentRunner
from app.db.database import Database
from app.models.core import MigrationJob
from app.pipeline.orchestrator import MigrationOrchestrator
from app.providers.mock_provider import MockProvider
from app.providers.router import ModelRouter
from app.services.workspace import WorkspaceService


def test_fake_end_to_end(tmp_path):
    database = Database(str(tmp_path / "db.sqlite"))
    provider = MockProvider()
    runner = AgentRunner({"mock": provider}, ModelRouter({"mock": provider}), database)
    job = MigrationJob(source_url="https://example.org/", max_cost_usd=3)
    database.save_job(job)
    result = asyncio.run(MigrationOrchestrator(database, runner, WorkspaceService(str(tmp_path / "workspaces"))).run(job))
    assert result.state.value == "COMPLETE", result.error
    assert len(database.get_usage(job.id)) == 11
    assert (Path(result.workspace_path) / "artifacts" / "evaluation.json").exists()
    assert (Path(result.workspace_path) / "reports" / "final-report-de.md").exists()
