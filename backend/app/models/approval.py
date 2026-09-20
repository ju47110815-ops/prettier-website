from __future__ import annotations
from pydantic import BaseModel
from enum import Enum

class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalPolicy(BaseModel):
    auto_allowed: list[str] = ["read_workspace", "write_workspace", "build", "test", "lint", "crawl_public_site"]
    requires_approval: list[str] = ["git_push", "production_deployment", "dns_change", "email", "paid_external_side_effect", "destructive_filesystem", "sensitive_credentials"]

class ApprovalRequest(BaseModel):
    id: str
    job_id: str
    action: str
    description: str
    decision: ApprovalDecision | None = None
