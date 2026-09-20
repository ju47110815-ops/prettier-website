from __future__ import annotations

import subprocess
import time
from pathlib import Path


class WorkspaceCommandService:
    def __init__(self, allowed_commands: set[str] | None = None):
        self.allowed_commands = allowed_commands or {"npm", "npx", "python", "pytest"}

    def run(self, command: list[str], workspace: str | Path, timeout: int = 300):
        if not command or Path(command[0]).name not in self.allowed_commands: raise PermissionError("Command is not allowlisted")
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=Path(workspace), capture_output=True, text=True, timeout=timeout, shell=False)
        return {"command": command, "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "duration": time.perf_counter() - started}
