from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Deque, Iterable, List, Optional, Set

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import ScrapeConfig
from .types import Article

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base error for scraper issues."""


@dataclass
class ScrapeStatistics:
    fetched: int = 0
    skipped: int = 0
    failed: int = 0


class ITSScraper:
    def __init__(self, config: ScrapeConfig, client: Optional[httpx.AsyncClient] = None):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = client
        self._external_client = client is not None
        self._semaphore = asyncio.Semaphore(config.concurrency)
        self._visited: Set[str] = set()
        self.stats = ScrapeStatistics()
        self._existing_sources: Set[str] = set()

    async def __aenter__(self) -> "ITSScraper":
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self.config.user_agent},
                timeout=self.config.request_timeout,
                follow_redirects=True,
            )
        if self.config.update_only:
            self._load_existing_sources()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client and not self._external_client:
            await self._client.aclose()

    async def fetch_html(self, url: str) -> str:
        assert self._client is not None, "Scraper must be used as async context manager"

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.config.retry_attempts),
            wait=wait_exponential(multiplier=self.config.retry_backoff, min=1),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,
        ):
            with attempt:
                async with self._semaphore:
                    if self.config.delay_between_requests:
                        await asyncio.sleep(self.config.delay_between_requests)
                    response = await self._client.get(url)
                    response.raise_for_status()
                    return response.text

        raise ScraperError(f"Unable to fetch {url}")

    async def _iter_article_urls(self) -> Iterable[str]:
        to_visit: Deque[str] = deque([self.config.start_url])
        seen_pages: Set[str] = set()

        while to_visit:
            page_url = to_visit.popleft()
            if page_url in seen_pages:
                continue
            seen_pages.add(page_url)

            try:
                html = await self.fetch_html(page_url)
            except (httpx.HTTPError, RetryError) as exc:
                logger.warning("Failed to load list page %s: %s", page_url, exc)
                continue

            soup = BeautifulSoup(html, "html.parser")
            for link in soup.select(self.config.article_link_selector):
                target = link.get(self.config.link_attribute)
                if not target:
                    continue
                if target.startswith("/"):
                    # Resolve relative paths
                    target = str(httpx.URL(page_url).join(target))

                if target not in self._visited:
                    self._visited.add(target)
                    yield target
                    if self.config.limit and len(self._visited) >= self.config.limit:
                        return

            if self.config.next_page_selector:
                next_link = soup.select_one(self.config.next_page_selector)
                if next_link:
                    href = next_link.get(self.config.link_attribute)
                    if href:
                        next_url = str(httpx.URL(page_url).join(href))
                        if next_url not in seen_pages:
                            to_visit.append(next_url)

    async def _scrape_article(self, url: str) -> Optional[Article]:
        if self.config.update_only and url in self._existing_sources:
            logger.debug("Skipping %s (already present)", url)
            self.stats.skipped += 1
            return None
        try:
            html = await self.fetch_html(url)
        except (httpx.HTTPError, RetryError) as exc:
            logger.error("Failed to fetch article %s: %s", url, exc)
            self.stats.failed += 1
            return None

        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.select_one(self.config.article_title_selector)
        content_node = soup.select_one(self.config.article_content_selector)

        if not title_node or not content_node:
            logger.warning("Missing title/content for %s", url)
            self.stats.failed += 1
            return None

        content_text = content_node.get_text(separator="\n", strip=True)
        content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        word_count = len(content_text.split())
        excerpt = content_text[:280] + ("…" if len(content_text) > 280 else "")

        article = Article(
            url=url,
            title=title_node.get_text(strip=True),
            content_html=str(content_node),
            content_text=content_text,
            fetched_at=datetime.now(timezone.utc),
            content_hash=content_hash,
            word_count=word_count,
            excerpt=excerpt,
            tags=[tag.get_text(strip=True) for tag in soup.select(".tags__item")],
            breadcrumbs=[
                crumb.get_text(strip=True) for crumb in soup.select(".breadcrumb a")
            ],
            meta={
                "source": url,
                "canonical": self._extract_canonical(soup),
            },
        )

        self.stats.fetched += 1
        return article

    async def scrape(self) -> List[Article]:
        articles: List[Article] = []
        async for url in self._iter_article_urls():
            article = await self._scrape_article(url)
            if article:
                articles.append(article)
        return articles

    @staticmethod
    def _extract_canonical(soup: BeautifulSoup) -> Optional[str]:
        canonical = soup.find("link", rel="canonical")
        if canonical:
            return canonical.get("href")
        return None

    def _load_existing_sources(self) -> None:
        base_dir = Path(self.config.output_directory)
        if not base_dir.exists():
            return
        metadata_files = base_dir.rglob(self.config.metadata_filename)
        for path in metadata_files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            source = (
                data.get("meta", {}).get("source")
                or data.get("meta", {}).get("canonical")
                or data.get("url")
            )
            if isinstance(source, str):
                self._existing_sources.add(source)

