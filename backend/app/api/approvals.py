from fastapi import APIRouter

router = APIRouter(prefix="/api/jobs", tags=["approvals"])

@router.post("/{job_id}/approvals/{approval_id}")
def decide_approval(job_id: str, approval_id: str, decision: str = "approved"):
    return {"job_id": job_id, "approval_id": approval_id, "decision": decision}
