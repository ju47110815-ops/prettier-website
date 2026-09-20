from __future__ import annotations

import json
from pathlib import Path

from app.models.core import EvaluationResult, QualityMetrics


class EvaluationService:
    def __init__(self, database):
        self.database = database

    def evaluate(self, job, workspace: str, quality: QualityMetrics) -> EvaluationResult:
        records = self.database.get_usage(job.id)
        result = EvaluationResult(job_id=job.id, routing_profile=job.routing_profile, models_used=sorted({f"{r.provider}/{r.model}" for r in records}), total_cost_usd=sum(r.estimated_cost_usd for r in records), total_model_calls=len(records), total_retries=sum(r.retries for r in records), total_tokens=sum(r.input_tokens + r.output_tokens for r in records), quality=quality, final_status=job.state.value)
        artifacts = Path(workspace) / "artifacts"
        reports = Path(workspace) / "reports"
        artifacts.mkdir(exist_ok=True); reports.mkdir(exist_ok=True)
        (artifacts / "evaluation.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
        (reports / "evaluation.md").write_text(f"# Evaluation\n\n- Profile: {job.routing_profile}\n- Total cost: ${result.total_cost_usd:.4f}\n- Model calls: {result.total_model_calls}\n- Build: {'PASS' if quality.production_build_passed else 'FAIL'}\n", encoding="utf-8")
        (reports / "final-report-de.md").write_text(f"# Migrationsbericht\n\n- Ausgangswebsite: {job.source_url}\n- Nutzerwunsch: {job.user_prompt}\n- Providerprofil: {job.routing_profile}\n- Modellkosten: ${result.total_cost_usd:.4f}\n- Build: {'ERFOLG' if quality.production_build_passed else 'FEHLER'}\n- Manuelle Pruefung: sensible Fakten und rechtliche Inhalte bestaetigen.\n", encoding="utf-8")
        return result
