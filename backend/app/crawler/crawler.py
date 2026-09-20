from __future__ import annotations

import asyncio
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse

import httpx

from app.models.core import CrawlPage, CrawlSnapshot
from app.crawler.extractor import extract_page


class BoundedCrawler:
    def __init__(self, *, max_pages: int = 100, max_depth: int = 5, max_page_bytes: int = 2_000_000, timeout: float = 15.0, max_assets: int = 500, client: httpx.AsyncClient | None = None):
        self.max_pages, self.max_depth, self.max_page_bytes, self.timeout, self.max_assets = max_pages, max_depth, max_page_bytes, timeout, max_assets
        self.client = client

    @staticmethod
    def normalize(url: str) -> str:
        url, _ = urldefrag(url)
        parsed = urlparse(url)
        path = parsed.path or "/"
        if path != "/": path = path.rstrip("/")
        return parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower(), path=path).geturl()

    async def crawl(self, source_url: str) -> CrawlSnapshot:
        source_url = self.normalize(source_url)
        host = urlparse(source_url).netloc
        queue = deque([(source_url, 0)])
        visited: set[str] = set()
        pages: list[CrawlPage] = []
        own_client = self.client is None
        client = self.client or httpx.AsyncClient(follow_redirects=True, timeout=self.timeout, headers={"User-Agent": "website-migration-engine/0.1"})
        try:
            while queue and len(pages) < self.max_pages:
                url, depth = queue.popleft()
                if url in visited or depth > self.max_depth: continue
                visited.add(url)
                try:
                    response = await client.get(url)
                    content = response.content[:self.max_page_bytes]
                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type: continue
                    page = extract_page(str(response.url), response.status_code, content.decode(response.encoding or "utf-8", errors="replace"), depth)
                    pages.append(page)
                    if depth < self.max_depth:
                        for link in page.internal_links:
                            normalized = self.normalize(urljoin(source_url, link))
                            if urlparse(normalized).netloc == host and normalized not in visited:
                                queue.append((normalized, depth + 1))
                except Exception as exc:
                    pages.append(CrawlPage(url=url, depth=depth, error=str(exc)))
            return CrawlSnapshot(source_url=source_url, pages=pages, truncated=bool(queue))
        finally:
            if own_client: await client.aclose()
