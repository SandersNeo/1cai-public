from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class OutputFormat(str, Enum):
    json = "json"
    markdown = "markdown"
    txt = "txt"

    @classmethod
    def list(cls) -> List[str]:
        return [cls.json, cls.markdown, cls.txt]


class ScrapeConfig(BaseModel):
    """Declarative configuration for the scraper."""

    start_url: str = Field(
        ...,
        description="Entry point (list page) that contains article links.",
    )
    article_link_selector: str = Field(
        "a.article-list__item",
        description="CSS selector that matches article links on the list page.",
    )
    next_page_selector: Optional[str] = Field(
        None,
        description="Optional CSS selector for pagination link to the next page.",
    )
    article_title_selector: str = Field(
        "h1",
        description="CSS selector that matches the article title.",
    )
    article_content_selector: str = Field(
        "[data-role='content'], .article-content",
        description="CSS selector that matches core article content.",
    )
    link_attribute: str = Field(
        "href",
        description="Attribute name that contains the article URL.",
    )
    formats: List[OutputFormat] = Field(
        default_factory=lambda: [OutputFormat.json],
        description="Formats to generate for every article.",
    )
    limit: Optional[int] = Field(
        None,
        description="Limit amount of articles (None disables limiting).",
    )
    concurrency: int = Field(
        5, ge=1, le=16, description="Maximum amount of concurrent HTTP requests."
    )
    request_timeout: float = Field(
        45.0, gt=0, description="HTTP timeout (seconds) for individual requests."
    )
    retry_attempts: int = Field(
        4, ge=0, description="How many times to retry failed HTTP requests."
    )
    retry_backoff: float = Field(
        2.0, ge=0, description="Backoff multiplier (seconds) between retries."
    )
    user_agent: str = Field(
        "1C-AI-ITS-Scraper/1.0 (+https://github.com/DmitrL-dev/1cai-public)",
        description="User agent string used for HTTP requests.",
    )
    output_directory: Path = Field(
        Path("output/its-scraper"),
        description="Directory where scraped files will be stored.",
    )
    update_only: bool = Field(
        False,
        description="If True, skip already downloaded articles (based on metadata).",
    )
    metadata_filename: str = Field(
        "metadata.json",
        description="Filename (relative to article folder) for metadata cache.",
    )
    rag_metadata: bool = Field(
        True,
        description="Store additional metadata fields to simplify RAG ingestion.",
    )
    verbose: bool = Field(
        False,
        description="Enable verbose logging.",
    )
    delay_between_requests: float = Field(
        0.0,
        ge=0.0,
        description="Delay (seconds) between HTTP requests to reduce load on ITS.",
    )

    @field_validator("formats", mode="before")
    def _normalize_formats(cls, value: Iterable[str]) -> List[OutputFormat]:
        formats: List[OutputFormat] = []
        for fmt in value:
            if isinstance(fmt, OutputFormat):
                fmt_lower = fmt.value
            else:
                fmt_lower = str(fmt).lower()
            if fmt_lower not in OutputFormat.list():
                raise ValueError(f"Unsupported format: {fmt}")
            formats.append(OutputFormat(fmt_lower))
        if not formats:
            raise ValueError("At least one format must be specified")
        return formats

    @classmethod
    def from_json(cls, path: Path) -> "ScrapeConfig":
        return cls.parse_obj(json.loads(path.read_text(encoding="utf-8")))

    def to_json(self, path: Path) -> None:
        path.write_text(self.json(indent=2, ensure_ascii=False), encoding="utf-8")


DEFAULT_CONFIG = ScrapeConfig(start_url="https://its.1c.ru/db/cabinetdoc")

