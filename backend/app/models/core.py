from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ModelTier(str, Enum):
    CHEAP = "cheap"
    STANDARD = "standard"
    STRONG = "strong"
    CODE = "code"
    REASONING = "reasoning"


class JobState(str, Enum):
    QUEUED = "QUEUED"
    PREFLIGHT = "PREFLIGHT"
    CRAWLING = "CRAWLING"
    RESEARCHING = "RESEARCHING"
    RESEARCH_COMPLETE = "RESEARCH_COMPLETE"
    ARCHITECTING = "ARCHITECTING"
    ARCHITECTURE_COMPLETE = "ARCHITECTURE_COMPLETE"
    MIGRATING = "MIGRATING"
    BUILDING = "BUILDING"
    CONTENT_INTEGRATION = "CONTENT_INTEGRATION"
    VALIDATING = "VALIDATING"
    QA = "QA"
    FIXING = "FIXING"
    EVALUATING = "EVALUATING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Capability(str, Enum):
    STRUCTURED_OUTPUT = "structured_output"
    JSON_OUTPUT = "json_output"
    TOOL_CALLING = "tool_calling"
    REASONING = "reasoning"


class AgentDefinition(BaseModel):
    id: str
    name: str
    purpose: str
    instructions: str = "Instructions will be supplied separately."
    preferred_model_tier: ModelTier = ModelTier.CHEAP
    fallback_model_tier: ModelTier | None = ModelTier.STANDARD
    allowed_tools: list[str] = Field(default_factory=list)
    input_type: str = "dict"
    output_type: str = "dict"
    max_input_tokens: int = 12000
    max_output_tokens: int = 4000
    max_steps: int = 1
    max_retries: int = 1
    max_cost_usd: float | None = None
    required_capabilities: list[Capability] = Field(default_factory=list)


class AgentUsage(BaseModel):
    request_count: int = 0
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    retries: int = 0


class UsageRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    job_id: str
    agent_id: str
    phase: str
    provider: str
    model: str
    model_tier: ModelTier
    request_count: int = 1
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    latency_ms: int = 0
    retries: int = 0
    estimated_cost_usd: float = 0.0
    provider_reported_cost_usd: float | None = None
    timestamp: datetime = Field(default_factory=utc_now)


class JobUsage(AgentUsage):
    job_id: str = ""
    by_phase: dict[str, AgentUsage] = Field(default_factory=dict)
    by_agent: dict[str, AgentUsage] = Field(default_factory=dict)


class MigrationJob(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_url: HttpUrl
    user_prompt: str = ""
    routing_profile: str = "cheap-deepseek"
    state: JobState = JobState.QUEUED
    current_phase: str = "queued"
    workspace_path: str = ""
    qa_iteration: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    error: str | None = None
    preview_url: str | None = None
    final_report_path: str | None = None
    max_cost_usd: float = 3.0
    current_cost_usd: float = 0.0


class CrawlPage(BaseModel):
    url: str
    status: int | None = None
    title: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    headings: list[str] = Field(default_factory=list)
    visible_text: str = ""
    internal_links: list[str] = Field(default_factory=list)
    external_links: list[str] = Field(default_factory=list)
    asset_references: list[str] = Field(default_factory=list)
    content_hash: str = ""
    depth: int = 0
    error: str | None = None


class CrawlSnapshot(BaseModel):
    source_url: str
    pages: list[CrawlPage] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=utc_now)
    truncated: bool = False


class ProviderCapabilities(BaseModel):
    structured_output: bool = False
    json_output: bool = False
    tool_calling: bool = False
    reasoning: bool = False
    context_size: int = 0
    max_output: int = 0


class ModelResponse(BaseModel):
    text: str = ""
    structured: Any = None
    provider: str
    model: str
    usage: AgentUsage = Field(default_factory=AgentUsage)
    finish_reason: str | None = None


class ValidationResult(BaseModel):
    name: str
    passed: bool
    details: str = ""
    errors: list[str] = Field(default_factory=list)


class QaIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    severity: Literal["BLOCKER", "HIGH", "MEDIUM", "LOW"]
    title: str
    description: str
    source: str = ""
    resolved: bool = False


class QaResult(BaseModel):
    passed: bool
    issues: list[QaIssue] = Field(default_factory=list)
    human_blockers: list[HumanBlocker] = Field(default_factory=list)


class HumanBlocker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: str
    title: str
    description: str
    source: str = ""
    blocking: bool = True
    suggested_action: str = ""
    resolution_status: str = "OPEN"


class QualityMetrics(BaseModel):
    production_build_passed: bool = False
    test_suite_passed: bool = False
    internal_broken_links: int = 0
    missing_assets: int = 0
    unresolved_placeholders: int = 0
    redirect_coverage: float = 0.0
    content_migration_coverage: float = 0.0
    source_pages_discovered: int = 0
    source_pages_selected_for_migration: int = 0
    source_pages_migrated: int = 0
    blocker_qa_issues: int = 0
    high_qa_issues: int = 0
    medium_qa_issues: int = 0
    low_qa_issues: int = 0
    human_blockers: int = 0
    qa_iterations: int = 0


class EvaluationResult(BaseModel):
    job_id: str
    routing_profile: str
    models_used: list[str] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    cost_by_phase: dict[str, float] = Field(default_factory=dict)
    total_model_calls: int = 0
    total_retries: int = 0
    total_tokens: int = 0
    total_duration_seconds: float = 0.0
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    qa_issues: list[QaIssue] = Field(default_factory=list)
    human_blockers: list[HumanBlocker] = Field(default_factory=list)
    final_status: str = ""


class FinalReport(BaseModel):
    evaluation: EvaluationResult
    german_markdown: str = ""


class ContentResearchResult(BaseModel):
    pages: list[str] = Field(default_factory=list)
    summary: str = ""


class UrlResearchResult(BaseModel):
    urls: list[str] = Field(default_factory=list)
    redirects: dict[str, str] = Field(default_factory=dict)
    summary: str = ""


class AssetResearchResult(BaseModel):
    assets: list[str] = Field(default_factory=list)
    summary: str = ""


class UxAuditResult(BaseModel):
    findings: list[str] = Field(default_factory=list)
    summary: str = ""


class ResearchBundle(BaseModel):
    content: ContentResearchResult = Field(default_factory=ContentResearchResult)
    urls: UrlResearchResult = Field(default_factory=UrlResearchResult)
    assets: AssetResearchResult = Field(default_factory=AssetResearchResult)
    ux: UxAuditResult = Field(default_factory=UxAuditResult)
    failures: list[str] = Field(default_factory=list)


class InformationArchitectureResult(BaseModel):
    navigation: list[str] = Field(default_factory=list)


class ContentModelResult(BaseModel):
    content_types: list[str] = Field(default_factory=list)


class TechnicalArchitectureResult(BaseModel):
    stack: str = ""
    decisions: list[str] = Field(default_factory=list)


class DesignStrategyResult(BaseModel):
    principles: list[str] = Field(default_factory=list)


class ArchitectureBundle(BaseModel):
    information_architecture: InformationArchitectureResult = Field(default_factory=InformationArchitectureResult)
    content_model: ContentModelResult = Field(default_factory=ContentModelResult)
    technical: TechnicalArchitectureResult = Field(default_factory=TechnicalArchitectureResult)
    design: DesignStrategyResult = Field(default_factory=DesignStrategyResult)


class MigrationResult(BaseModel):
    migrated_pages: int = 0
    notes: list[str] = Field(default_factory=list)


class ImplementationResult(BaseModel):
    build_command: str = ""
    output_path: str = ""
    notes: list[str] = Field(default_factory=list)
