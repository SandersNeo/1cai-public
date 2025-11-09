"""
Advanced scraper for 1C ITS content with retries, rate limiting and flexible output.

This module integrates the enhanced scraping pipeline into the 1C AI Stack project.
It is intentionally self-contained so it can be reused both from the CLI and from
automation workflows (Make targets, orchestrator jobs, CI tasks).
"""

from .config import ScrapeConfig, OutputFormat, DEFAULT_CONFIG
from .scraper import ITSScraper, ScrapeStatistics

__all__ = [
    "ScrapeConfig",
    "OutputFormat",
    "DEFAULT_CONFIG",
    "ITSScraper",
    "ScrapeStatistics",
]

