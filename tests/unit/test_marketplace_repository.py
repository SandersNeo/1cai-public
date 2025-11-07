"""Unit tests for MarketplaceRepository helpers that do not touch the database."""

from typing import Any, Dict

import pytest

from src.db.marketplace_repository import MarketplaceRepository


class DummyS3Client:
    def __init__(self, url: str) -> None:
        self.url = url

    def generate_presigned_url(self, *_args, **_kwargs):  # noqa: D401, ANN003
        """Return deterministic URL for testing."""
        return self.url


def _create_repo(storage: Dict[str, str]) -> MarketplaceRepository:
    repo = MarketplaceRepository(pool=None, cache=None, storage_config=storage)  # type: ignore[arg-type]
    return repo


@pytest.mark.asyncio()
async def test_build_download_payload_fallback() -> None:
    repo = _create_repo({})
    plugin = {
        "plugin_id": "plugin-demo",
        "download_url": "https://cdn.example.com/plugin-demo.zip",
        "artifact_path": None,
    }

    payload = await repo.build_download_payload(plugin)

    assert payload["download_url"] == "https://cdn.example.com/plugin-demo.zip"
    assert payload["status"] == "ready"


@pytest.mark.asyncio()
async def test_build_download_payload_presigned() -> None:
    repo = _create_repo({"bucket": "test", "region": "us-test-1"})
    repo._s3_client = DummyS3Client("https://s3.example.com/presigned")  # type: ignore[attr-defined]

    plugin: Dict[str, Any] = {
        "plugin_id": "plugin-demo",
        "download_url": "https://legacy.example.com/plugin-demo.zip",
        "artifact_path": "artifacts/plugin-demo.zip",
    }

    payload = await repo.build_download_payload(plugin)

    assert payload["download_url"] == "https://s3.example.com/presigned"
    assert "manifest.json" in payload["files"]

