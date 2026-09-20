from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl

from app.models.core import JobState, MigrationJob

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    source_url: HttpUrl
    user_prompt: str = ""
    routing_profile: str = "cheap-deepseek"
    max_cost_usd: float = 3.0


def services():
    from app.main import database, orchestrator, tasks
    return database, orchestrator, tasks


@router.post("")
async def create_job(request: CreateJobRequest):
    database, orchestrator, tasks = services()
    job = MigrationJob(source_url=request.source_url, user_prompt=request.user_prompt, routing_profile=request.routing_profile, max_cost_usd=request.max_cost_usd)
    database.save_job(job)
    tasks[job.id] = asyncio.create_task(orchestrator.run(job))
    return {"job_id": job.id, "state": job.state.value}


@router.get("")
def list_jobs():
    return services()[0].list_jobs()


@router.get("/{job_id}")
def get_job(job_id: str):
    job = services()[0].get_job(job_id)
    if not job: raise HTTPException(404, "Job not found")
    return job


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str):
    database, _, tasks = services()
    job = database.get_job(job_id)
    if not job: raise HTTPException(404, "Job not found")
    task = tasks.get(job_id)
    if task and not task.done(): task.cancel()
    job.state = JobState.CANCELLED; database.save_job(job)
    return job


@router.get("/{job_id}/usage")
def usage(job_id: str):
    return services()[0].get_usage(job_id)


@router.get("/{job_id}/metrics")
def metrics(job_id: str):
    database = services()[0]; job = database.get_job(job_id)
    if not job: raise HTTPException(404, "Job not found")
    records = database.get_usage(job_id)
    return {"total_cost_usd": sum(record.estimated_cost_usd for record in records), "total_model_calls": len(records), "total_tokens": sum(record.input_tokens + record.output_tokens for record in records), "qa_iterations": job.qa_iteration}


@router.get("/{job_id}/evaluation")
def evaluation(job_id: str):
    database = services()[0]; job = database.get_job(job_id)
    if not job: raise HTTPException(404, "Job not found")
    path = Path(job.workspace_path) / "artifacts" / "evaluation.json"
    if not path.exists(): raise HTTPException(404, "Evaluation not available")
    return path.read_text(encoding="utf-8")


@router.get("/{job_id}/report")
def report(job_id: str):
    database = services()[0]; job = database.get_job(job_id)
    if not job or not job.final_report_path: raise HTTPException(404, "Report not available")
    return FileResponse(job.final_report_path, media_type="text/markdown")


@router.get("/{job_id}/blockers")
def blockers(job_id: str):
    return []


@router.get("/{job_id}/approvals")
def approvals(job_id: str):
    return []
