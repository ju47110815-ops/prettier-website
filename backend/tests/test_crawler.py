import httpx
import pytest

from app.crawler.crawler import BoundedCrawler


@pytest.mark.asyncio
async def test_crawler_is_bounded_and_same_domain():
    pages = {
        "https://example.org/": '<a href="/one">one</a><a href="https://other.test/x">external</a>',
        "https://example.org/one": '<a href="/two">two</a>',
        "https://example.org/two": '<p>two</p>',
    }

    async def handler(request):
        return httpx.Response(200, headers={"content-type": "text/html"}, text=pages.get(str(request.url), ""))

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    snapshot = await BoundedCrawler(max_pages=2, client=client).crawl("https://EXAMPLE.org/#fragment")
    await client.aclose()
    assert len(snapshot.pages) == 2
    assert all("other.test" not in link for page in snapshot.pages for link in page.internal_links)
