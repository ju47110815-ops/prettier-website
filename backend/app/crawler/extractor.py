from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from app.models.core import CrawlPage


class PageParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self.headings: list[str] = []
        self.text: list[str] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.meta: dict[str, str] = {}
        self._title = False
        self._heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "title": self._title = True
        if tag in {"h1", "h2", "h3"}: self._heading = True
        if tag == "meta" and attrs_dict.get("name") and attrs_dict.get("content"):
            self.meta[attrs_dict["name"]] = attrs_dict["content"] or ""
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(urljoin(self.base_url, attrs_dict["href"]))
        if tag in {"img", "script", "link", "source"}:
            value = attrs_dict.get("src") or attrs_dict.get("href")
            if value: self.assets.append(urljoin(self.base_url, value))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title": self._title = False
        if tag in {"h1", "h2", "h3"}: self._heading = False

    def handle_data(self, data: str) -> None:
        cleaned = re.sub(r"\s+", " ", data).strip()
        if not cleaned: return
        if self._title: self.title += cleaned
        elif self._heading: self.headings.append(cleaned)
        else: self.text.append(cleaned)


def extract_page(url: str, status: int, html: str, depth: int = 0) -> CrawlPage:
    parser = PageParser(url)
    parser.feed(html)
    visible_text = " ".join(parser.text)
    internal, external = [], []
    source_host = urlparse(url).netloc.lower()
    for link in parser.links:
        (internal if urlparse(link).netloc.lower() == source_host else external).append(link)
    return CrawlPage(url=url, status=status, title=parser.title, metadata=parser.meta, headings=parser.headings, visible_text=visible_text, internal_links=sorted(set(internal)), external_links=sorted(set(external)), asset_references=sorted(set(parser.assets)), content_hash=hashlib.sha256(visible_text.encode()).hexdigest(), depth=depth)
