from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.models.core import JobState, MigrationJob, UsageRecord, utc_now


class Database:
    def __init__(self, path: str = "./workspaces/migration.db"):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, source_url TEXT NOT NULL, user_prompt TEXT NOT NULL,
            routing_profile TEXT NOT NULL, state TEXT NOT NULL, current_phase TEXT NOT NULL,
            workspace_path TEXT NOT NULL, qa_iteration INTEGER NOT NULL, created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL, error TEXT, preview_url TEXT, final_report_path TEXT,
            max_cost_usd REAL NOT NULL, current_cost_usd REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS usage_records (
            id TEXT PRIMARY KEY, job_id TEXT NOT NULL, agent_id TEXT NOT NULL, phase TEXT NOT NULL,
            provider TEXT NOT NULL, model TEXT NOT NULL, model_tier TEXT NOT NULL,
            request_count INTEGER NOT NULL, input_tokens INTEGER NOT NULL, cached_input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL, reasoning_tokens INTEGER NOT NULL, latency_ms INTEGER NOT NULL,
            retries INTEGER NOT NULL, estimated_cost_usd REAL NOT NULL, provider_reported_cost_usd REAL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS artifacts (job_id TEXT NOT NULL, name TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(job_id, name));
        """)
        self.connection.commit()

    def save_job(self, job: MigrationJob) -> MigrationJob:
        job.updated_at = utc_now()
        values = job.model_dump(mode="json")
        self.connection.execute("""INSERT OR REPLACE INTO jobs VALUES (:id,:source_url,:user_prompt,:routing_profile,:state,:current_phase,:workspace_path,:qa_iteration,:created_at,:updated_at,:error,:preview_url,:final_report_path,:max_cost_usd,:current_cost_usd)""", values)
        self.connection.commit()
        return job

    def get_job(self, job_id: str) -> MigrationJob | None:
        row = self.connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return MigrationJob.model_validate(dict(row)) if row else None

    def list_jobs(self) -> list[MigrationJob]:
        return [MigrationJob.model_validate(dict(row)) for row in self.connection.execute("SELECT * FROM jobs ORDER BY created_at DESC")]

    def add_usage(self, record: UsageRecord) -> None:
        self.connection.execute("""INSERT INTO usage_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", tuple(record.model_dump(mode="json").values()))
        self.connection.commit()

    def get_usage(self, job_id: str) -> list[UsageRecord]:
        return [UsageRecord.model_validate(dict(row)) for row in self.connection.execute("SELECT * FROM usage_records WHERE job_id = ? ORDER BY timestamp", (job_id,))]

    def save_artifact(self, job_id: str, name: str, value: Any) -> None:
        serialized = value if isinstance(value, str) else json.dumps(value, default=str, indent=2)
        self.connection.execute("INSERT OR REPLACE INTO artifacts VALUES (?,?,?)", (job_id, name, serialized))
        self.connection.commit()

    def get_artifact(self, job_id: str, name: str) -> str | None:
        row = self.connection.execute("SELECT value FROM artifacts WHERE job_id = ? AND name = ?", (job_id, name)).fetchone()
        return row[0] if row else None
