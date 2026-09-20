from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/jobs", tags=["events"])


@router.get("/{job_id}/events")
async def events(job_id: str):
    from app.main import database
    if not database.get_job(job_id): raise HTTPException(404, "Job not found")
    async def stream():
        last = None
        for _ in range(120):
            job = database.get_job(job_id)
            current = (job.state.value, job.current_phase, job.current_cost_usd)
            if current != last:
                yield f"data: {{\"state\": \"{current[0]}\", \"phase\": \"{current[1]}\", \"cost\": {current[2]}}}\n\n"
                last = current
            if job.state.value in {"COMPLETE", "FAILED", "CANCELLED", "BUDGET_EXCEEDED"}: break
            await asyncio.sleep(0.25)
    return StreamingResponse(stream(), media_type="text/event-stream")
