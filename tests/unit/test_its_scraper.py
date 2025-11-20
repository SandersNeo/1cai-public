# [NEXUS IDENTITY] ID: -9044220303696958570 | DATE: 2025-11-19

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

pytest.importorskip("bs4")
pytest.importorskip("markdownify")

from integrations.its_scraper import OutputFormat, ScrapeConfig
from integrations.its_scraper.scraper import ITSScraper
from integrations.its_scraper.types import Article
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
            results = await scraper.scrape()

        assert len(results) == 1
        article, existing_meta = results[0]
        paths = list(persist_article(article, config, existing_meta=existing_meta))

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


def test_persist_article_creates_versions(tmp_path: Path) -> None:
    config = ScrapeConfig(
        start_url="https://example.com/list",
        output_directory=tmp_path,
        formats=[OutputFormat.json],
        update_only=True,
    )

    first_article = Article(
        url="https://example.com/article-1",
        title="Article One",
        content_html="<p>Hello</p>",
        content_text="Hello",
        fetched_at=datetime.now(timezone.utc),
        content_hash="hash1",
        word_count=1,
        excerpt="Hello",
        meta={"canonical": "https://example.com/article-1"},
    )

    persisted = list(persist_article(first_article, config, existing_meta=None))
    assert persisted

    metadata_path = (
        tmp_path / slugify("https://example.com/article-1") / config.metadata_filename
    )
    existing_meta = json.loads(metadata_path.read_text(encoding="utf-8"))

    second_article = Article(
        url="https://example.com/article-1",
        title="Article One",
        content_html="<p>Hello World!</p>",
        content_text="Hello World!",
        fetched_at=datetime.now(timezone.utc),
        content_hash="hash2",
        word_count=2,
        excerpt="Hello World!",
        meta={"canonical": "https://example.com/article-1"},
    )

    persisted_second = list(
        persist_article(second_article, config, existing_meta=existing_meta)
    )
    assert persisted_second

    versions_dir = metadata_path.parent / "versions"
    assert versions_dir.exists()
    assert any(versions_dir.iterdir())
    new_meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert new_meta["meta"]["previous_version"] == existing_meta.get("fetched_at")
