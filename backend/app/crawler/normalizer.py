from __future__ import annotations

import re

from app.models.core import CrawlPage, CrawlSnapshot


def preprocess_snapshot(snapshot: CrawlSnapshot, max_text_chars: int = 12000) -> CrawlSnapshot:
    seen_hashes: set[str] = set()
    pages: list[CrawlPage] = []
    for page in snapshot.pages:
        page.visible_text = re.sub(r"\s+", " ", page.visible_text).strip()[:max_text_chars]
        if not page.visible_text and page.status == 200: continue
        if page.content_hash and page.content_hash in seen_hashes: continue
        seen_hashes.add(page.content_hash)
        pages.append(page)
    snapshot.pages = pages
    return snapshot
