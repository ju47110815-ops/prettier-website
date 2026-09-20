from __future__ import annotations

import re
from pathlib import Path

from app.models.core import ValidationResult


class ValidationSuite:
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace)

    def run(self) -> list[ValidationResult]:
        results = []
        generated = self.workspace / "generated-site"
        build_marker = generated / "BUILD_OK"
        results.append(ValidationResult(name="production_build", passed=build_marker.exists(), details="BUILD_OK marker present" if build_marker.exists() else "No successful build marker"))
        files = list(generated.rglob("*") if generated.exists() else [])
        placeholders = [str(path) for path in files if path.is_file() and re.search(r"TODO|PLACEHOLDER", path.read_text(encoding="utf-8", errors="ignore"))]
        results.append(ValidationResult(name="unresolved_placeholders", passed=not placeholders, details="; ".join(placeholders), errors=placeholders))
        return results
