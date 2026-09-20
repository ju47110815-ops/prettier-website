from dataclasses import dataclass

@dataclass
class PreviewService:
    command: list[str] | None = None
    port: int | None = None
    url: str | None = None
    running: bool = False

    def status(self):
        return {"command": self.command, "port": self.port, "url": self.url, "running": self.running}
