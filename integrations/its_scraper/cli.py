from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer

from .config import DEFAULT_CONFIG, OutputFormat, ScrapeConfig
from .scraper import ITSScraper
from .writers import persist_article

app = typer.Typer(help="Enhanced scraper for 1C ITS documentation.")


def _load_config(config_path: Optional[Path]) -> ScrapeConfig:
    if config_path:
        return ScrapeConfig.from_json(config_path)
    return DEFAULT_CONFIG


@app.command()
def scrape(
    start_url: str = typer.Argument(
        DEFAULT_CONFIG.start_url, help="Start URL that contains the article list."
    ),
    limit: Optional[int] = typer.Option(
        DEFAULT_CONFIG.limit,
        help="Limit amount of articles to download (default: unlimited).",
    ),
    format: Optional[list[OutputFormat]] = typer.Option(
        None,
        "--format",
        "-f",
        case_sensitive=False,
        help=f"Output formats ({', '.join(OutputFormat.list())}).",
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Optional path to JSON config that overrides defaults.",
    ),
    update_only: bool = typer.Option(
        False,
        "--update",
        help="Skip already downloaded articles (metadata must exist).",
    ),
    concurrency: Optional[int] = typer.Option(
        None,
        "--concurrency",
        "-n",
        help="Override concurrency (default from config).",
    ),
    sleep: Optional[float] = typer.Option(
        None,
        "--sleep",
        "-s",
        help="Delay between HTTP requests in seconds.",
    ),
    output_dir: Path = typer.Option(
        DEFAULT_CONFIG.output_directory,
        "--output",
        "-o",
        help="Directory for scraped files.",
    ),
) -> None:
    """
    Scrape ITS documentation starting from START_URL and produce the selected formats.
    """
    config = _load_config(config_path)
    config.start_url = start_url
    if limit is not None:
        config.limit = limit
    if format:
        config.formats = [OutputFormat(f.lower()) for f in format]
    if concurrency is not None:
        config.concurrency = concurrency
    if sleep is not None:
        config.delay_between_requests = sleep
    config.update_only = update_only
    config.output_directory = output_dir

    if config.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    async def _runner() -> None:
        async with ITSScraper(config) as scraper:
            articles = await scraper.scrape()
            for article in articles:
                files = list(persist_article(article, config))
                if not files and config.update_only:
                    scraper.stats.skipped += 1
            typer.echo(
                f"Fetched {scraper.stats.fetched}, "
                f"skipped {scraper.stats.skipped}, "
                f"failed {scraper.stats.failed}"
            )

    asyncio.run(_runner())


@app.command()
def generate_config(path: Path = typer.Argument(Path("its-scraper.config.json"))) -> None:
    """
    Generate default configuration file.
    """
    DEFAULT_CONFIG.to_json(path)
    typer.echo(f"Wrote config to {path}")


def main() -> None:  # pragma: no cover - entrypoint
    app()


if __name__ == "__main__":  # pragma: no cover
    main()

