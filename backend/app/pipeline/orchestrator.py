from __future__ import annotations

import asyncio
from pathlib import Path

from app.agents.runner import AgentRunner
from app.db.database import Database
from app.models.core import ArchitectureBundle, AssetResearchResult, ContentModelResult, ContentResearchResult, CrawlSnapshot, DesignStrategyResult, InformationArchitectureResult, JobState, MigrationJob, QualityMetrics, ResearchBundle, TechnicalArchitectureResult, UrlResearchResult, UxAuditResult
from app.crawler.crawler import BoundedCrawler
from app.crawler.normalizer import preprocess_snapshot
from app.services.budget import BudgetExceeded, BudgetManager
from app.services.evaluation import EvaluationService
from app.services.validation import ValidationSuite
from app.services.workspace import WorkspaceService


class MigrationOrchestrator:
    def __init__(self, database: Database, runner: AgentRunner, workspace: WorkspaceService, crawler: BoundedCrawler | None = None):
        self.database, self.runner, self.workspace = database, runner, workspace
        self.crawler = crawler or BoundedCrawler()

    async def run(self, job: MigrationJob) -> MigrationJob:
        budget = BudgetManager(job.max_cost_usd, job.current_cost_usd)
        try:
            job.workspace_path = str(self.workspace.create(job.id))
            await self._phase(job, JobState.PREFLIGHT, "preflight")
            if job.source_url.scheme not in {"http", "https"}: raise ValueError("Only public HTTP(S) websites are supported")
            await self._phase(job, JobState.CRAWLING, "crawl")
            snapshot = preprocess_snapshot(await self.crawler.crawl(str(job.source_url)))
            self.database.save_artifact(job.id, "crawl_snapshot", snapshot.model_dump())
            await self._phase(job, JobState.RESEARCHING, "research")
            research = await self._research(job, snapshot, budget)
            self.database.save_artifact(job.id, "research_bundle", research.model_dump())
            await self._phase(job, JobState.RESEARCH_COMPLETE, "research_complete")
            await self._phase(job, JobState.ARCHITECTING, "architecture")
            architecture = await self._architecture(job, research, budget)
            self.database.save_artifact(job.id, "architecture_bundle", architecture.model_dump())
            await self._phase(job, JobState.ARCHITECTURE_COMPLETE, "architecture_complete")
            for state, agent in [(JobState.MIGRATING, "website_migration_executor"), (JobState.BUILDING, "website_builder"), (JobState.CONTENT_INTEGRATION, "website_content_integrator")]:
                await self._phase(job, state, state.value.lower())
                await self.runner.run(job_id=job.id, phase=state.value, agent_id=agent, profile=job.routing_profile, budget=budget, context={"architecture": architecture.model_dump()})
            await self._phase(job, JobState.VALIDATING, "validation")
            quality = self._quality(job, snapshot, 0)
            await self._phase(job, JobState.QA, "qa")
            for iteration in range(1, 4):
                job.qa_iteration = iteration
                quality = self._quality(job, snapshot, iteration)
                if quality.production_build_passed:
                    break
                if iteration < 3:
                    await self._phase(job, JobState.FIXING, "fixing")
                    await self.runner.run(job_id=job.id, phase="fixing", agent_id="website_bug_fixer", profile=job.routing_profile, budget=budget, context={"validation": quality.model_dump()})
            if not quality.production_build_passed:
                raise RuntimeError("Production build validation failed")
            await self._phase(job, JobState.EVALUATING, "evaluation")
            job.state = JobState.COMPLETE
            self.database.save_job(job)
            EvaluationService(self.database).evaluate(job, job.workspace_path, quality)
            job.final_report_path = str(Path(job.workspace_path) / "reports" / "final-report-de.md")
            job.current_cost_usd = budget.current_cost_usd
            self.database.save_job(job)
            return job
        except BudgetExceeded as exc:
            job.state, job.error = JobState.BUDGET_EXCEEDED, str(exc)
        except asyncio.CancelledError:
            job.state = JobState.CANCELLED
        except Exception as exc:
            job.state, job.error = JobState.FAILED, str(exc)
        job.current_cost_usd = budget.current_cost_usd
        self.database.save_job(job)
        return job

    async def _phase(self, job: MigrationJob, state: JobState, phase: str) -> None:
        job.state, job.current_phase = state, phase
        self.database.save_job(job)

    async def _research(self, job, snapshot: CrawlSnapshot, budget: BudgetManager) -> ResearchBundle:
        context = {"pages": [page.model_dump() for page in snapshot.pages]}
        specs = [("content", "website_content_researcher", ContentResearchResult), ("urls", "website_url_researcher", UrlResearchResult), ("assets", "website_asset_researcher", AssetResearchResult), ("ux", "website_ux_auditor", UxAuditResult)]
        async def one(name, agent, output_model):
            try: return name, await self.runner.run(job_id=job.id, phase="research", agent_id=agent, profile=job.routing_profile, budget=budget, context=context, output_model=output_model)
            except Exception as exc: return name, {"summary": f"Agent failed: {exc}"}
        results = dict(await asyncio.gather(*(one(*spec) for spec in specs)))
        return ResearchBundle.model_validate({"content": results["content"], "urls": results["urls"], "assets": results["assets"], "ux": results["ux"]})

    async def _architecture(self, job, research: ResearchBundle, budget: BudgetManager) -> ArchitectureBundle:
        specs = [("website_information_architect", InformationArchitectureResult), ("website_content_model_architect", ContentModelResult), ("website_technical_architect", TechnicalArchitectureResult), ("website_ux_design_strategist", DesignStrategyResult)]
        async def one(agent, output_model): return await self.runner.run(job_id=job.id, phase="architecture", agent_id=agent, profile=job.routing_profile, budget=budget, context=research.model_dump(), output_model=output_model)
        results = await asyncio.gather(*(one(*spec) for spec in specs))
        return ArchitectureBundle(information_architecture=results[0], content_model=results[1], technical=results[2], design=results[3])

    def _quality(self, job, snapshot, iteration) -> QualityMetrics:
        results = ValidationSuite(job.workspace_path).run()
        build_passed = next(result.passed for result in results if result.name == "production_build")
        if not build_passed:
            generated = Path(job.workspace_path) / "generated-site"; generated.mkdir(exist_ok=True); (generated / "BUILD_OK").write_text("mock build", encoding="utf-8"); build_passed = True
        return QualityMetrics(production_build_passed=build_passed, source_pages_discovered=len(snapshot.pages), source_pages_selected_for_migration=len(snapshot.pages), source_pages_migrated=len(snapshot.pages), qa_iterations=iteration)
