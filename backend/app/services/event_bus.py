from __future__ import annotations

import asyncio

class EventBus:
    def __init__(self): self._events: dict[str, list[dict]] = {}
    def publish(self, job_id: str, event: dict): self._events.setdefault(job_id, []).append(event)
    async def subscribe(self, job_id: str):
        seen = 0
        while True:
            events = self._events.get(job_id, [])
            while seen < len(events): yield events[seen]; seen += 1
            await asyncio.sleep(0.25)
