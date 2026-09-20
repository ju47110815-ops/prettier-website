from __future__ import annotations

import argparse
import asyncio
import os

from app.agents.runner import AgentRunner
from app.db.database import Database
from app.models.core import MigrationJob
from app.pipeline.orchestrator import MigrationOrchestrator
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.mock_provider import MockProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.router import ModelRouter
from app.services.workspace import WorkspaceService


def build_orchestrator():
    database = Database(os.getenv("DATABASE_PATH", "./workspaces/migration.db"))
    providers = {"mock": MockProvider()}
    if os.getenv("OPENAI_API_KEY"): providers["openai"] = OpenAIProvider()
    if os.getenv("DEEPSEEK_API_KEY"): providers["deepseek"] = DeepSeekProvider()
    return database, MigrationOrchestrator(database, AgentRunner(providers, ModelRouter(providers), database), WorkspaceService(os.getenv("WORKSPACE_ROOT", "./workspaces")))

async def migrate(args):
    database, orchestrator = build_orchestrator()
    job = MigrationJob(source_url=args.url, user_prompt=args.prompt, routing_profile=args.profile, max_cost_usd=args.max_cost)
    database.save_job(job)
    print(f"job {job.id} QUEUED")
    result = await orchestrator.run(job)
    records = database.get_usage(job.id)
    print(f"state={result.state.value} phase={result.current_phase} calls={len(records)} cost=${result.current_cost_usd:.4f}")
    print(f"workspace={result.workspace_path}")
    if result.error: print(f"error={result.error}")


def show_job(args):
    database, _ = build_orchestrator(); job = database.get_job(args.job_id)
    if not job: raise SystemExit("job not found")
    print(job.model_dump_json(indent=2))


def compare(args):
    database, _ = build_orchestrator()
    rows = []
    for job_id in (args.job_a, args.job_b):
        job = database.get_job(job_id); records = database.get_usage(job_id) if job else []
        rows.append((job_id, job.routing_profile if job else "?", sum(r.estimated_cost_usd for r in records), len(records), job.state.value if job else "MISSING"))
    for row in rows: print(" | ".join(map(str, row)))


def main():
    parser = argparse.ArgumentParser(prog="website-migration-engine")
    sub = parser.add_subparsers(dest="command", required=True)
    migrate_parser = sub.add_parser("migrate"); migrate_parser.add_argument("--url", required=True); migrate_parser.add_argument("--prompt", default=""); migrate_parser.add_argument("--profile", default="cheap-deepseek"); migrate_parser.add_argument("--max-cost", type=float, default=3.0); migrate_parser.set_defaults(func=lambda args: asyncio.run(migrate(args)))
    job_parser = sub.add_parser("job"); job_parser.add_argument("job_id"); job_parser.set_defaults(func=show_job)
    compare_parser = sub.add_parser("compare"); compare_parser.add_argument("job_a"); compare_parser.add_argument("job_b"); compare_parser.set_defaults(func=compare)
    args = parser.parse_args(); args.func(args)

if __name__ == "__main__": main()
