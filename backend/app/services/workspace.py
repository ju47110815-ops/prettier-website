from __future__ import annotations

from pathlib import Path


class WorkspaceService:
    def __init__(self, root: str = "./workspaces"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, job_id: str) -> Path:
        path = self.safe_path(job_id)
        for name in ("crawl", "generated-site", "artifacts", "reports", "logs"):
            (path / name).mkdir(parents=True, exist_ok=True)
        return path

    def safe_path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Workspace path escapes workspace root")
        return candidate

    def resolve_file(self, job_id: str, relative: str) -> Path:
        workspace = self.safe_path(job_id)
        candidate = (workspace / relative).resolve()
        if candidate != workspace and workspace not in candidate.parents:
            raise ValueError("File path escapes job workspace")
        return candidate

    def write_text(self, job_id: str, relative: str, content: str) -> Path:
        path = self.resolve_file(job_id, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
