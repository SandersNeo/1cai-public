import json
from pathlib import Path

import httpx
import pytest

pytest.importorskip("bs4")
pytest.importorskip("markdownify")

from integrations.its_scraper import OutputFormat, ScrapeConfig
from integrations.its_scraper.scraper import ITSScraper
from integrations.its_scraper.writers import persist_article, slugify


def _mock_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/list":
        html = """
        <html>
            <body>
                <a class="article-list__item" href="/article-1">Article 1</a>
            </body>
        </html>
        """
        return httpx.Response(200, text=html)
    if request.url.path == "/article-1":
        html = """
        <html>
            <head>
                <title>Demo article</title>
                <link rel="canonical" href="https://example.com/article-1"/>
            </head>
            <body>
                <h1>Example Title</h1>
                <div data-role="content">
                    <p>Hello <strong>world</strong></p>
                </div>
                <div class="tags__item">Tag A</div>
                <div class="breadcrumb"><a>Root</a></div>
            </body>
        </html>
        """
        return httpx.Response(200, text=html)
    return httpx.Response(404)


@pytest.mark.asyncio
async def test_scraper_fetches_and_persists(tmp_path: Path) -> None:
    config = ScrapeConfig(
        start_url="https://example.com/list",
        article_link_selector="a.article-list__item",
        article_title_selector="h1",
        article_content_selector="[data-role='content']",
        formats=[OutputFormat.json, OutputFormat.markdown],
        output_directory=tmp_path,
        limit=5,
    )

    transport = httpx.MockTransport(_mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        async with ITSScraper(config, client=client) as scraper:
            articles = await scraper.scrape()

        assert len(articles) == 1
        article = articles[0]
        paths = list(persist_article(article, config))

    slug = slugify("https://example.com/article-1")
    article_dir = tmp_path / slug
    expected_files = {
        article_dir / "article.json",
        article_dir / "article.md",
        article_dir / config.metadata_filename,
    }
    assert set(paths) == expected_files

    metadata = json.loads((article_dir / config.metadata_filename).read_text("utf-8"))
    assert metadata["title"] == "Example Title"
    assert metadata["meta"]["canonical"] == "https://example.com/article-1"
    assert metadata["content_hash"]
    assert metadata["word_count"] > 0
    assert metadata["excerpt"].replace("\n", " ").startswith("Hello world")


def test_slugify_handles_unicode() -> None:
    assert slugify("Пример статьи 1") == "пример-статьи-1"

