from __future__ import annotations

from app.models.core import CrawlSnapshot

class ContextBuilder:
    def pages_for_agent(self, snapshot: CrawlSnapshot, urls: list[str] | None = None, max_chars: int = 12000) -> list[dict]:
        selected = [page for page in snapshot.pages if not urls or page.url in urls]
        return [{"url": page.url, "title": page.title, "headings": page.headings, "text": page.visible_text[:max_chars]} for page in selected]
