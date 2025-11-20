# [NEXUS IDENTITY] ID: -5710041942027674930 | DATE: 2025-11-19

import io

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.marketplace import (
    MAX_ARTIFACT_SIZE_BYTES,
    router as marketplace_router,
    get_marketplace_repository,
    get_current_user as marketplace_get_current_user,
)
from src.security.auth import CurrentUser


class DummyRepo:
    def __init__(
        self, plugin_exists: bool = True, fail_upload: Exception | None = None
    ):
        self.plugin_exists = plugin_exists
        self.fail_upload = fail_upload
        self.last_call = None

    async def get_plugin(self, plugin_id: str):
        if not self.plugin_exists:
            return None
        return {
            "id": plugin_id,
            "plugin_id": plugin_id,
            "name": "Test",
            "description": "Test plugin",
            "category": "ai_agent",
            "version": "1.0.0",
            "author": "tester",
            "status": "pending",
            "visibility": "public",
            "downloads": 0,
            "rating": 0.0,
            "ratings_count": 0,
            "installs": 0,
            "homepage": None,
            "repository": None,
            "download_url": "/marketplace/plugins/plugin/download",
            "icon_url": None,
            "screenshot_urls": [],
            "artifact_path": None,
            "license": "MIT",
            "keywords": [],
            "min_version": "1.0.0",
            "supported_platforms": [],
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "published_at": None,
            "featured": False,
            "verified": False,
            "owner_id": "user-1",
            "owner_username": "tester",
        }

    async def store_artifact(
        self, plugin_id: str, data: bytes, filename: str, content_type: str | None
    ):
        if self.fail_upload:
            raise self.fail_upload
        self.last_call = {
            "plugin_id": plugin_id,
            "data": data,
            "filename": filename,
            "content_type": content_type,
        }
        plugin = await self.get_plugin(plugin_id)
        plugin = plugin.copy()
        plugin["artifact_path"] = "marketplace/plugin/latest/artifact.zip"
        return plugin


def _make_app(repo: DummyRepo):
    app = FastAPI()
    app.include_router(marketplace_router)

    def fake_repo():
        return repo

    def fake_user():
        return CurrentUser(
            user_id="user-1",
            username="tester",
            roles={"developer"},
            permissions=set(),
            is_service=False,
        )

    app.dependency_overrides[get_marketplace_repository] = fake_repo
    app.dependency_overrides[marketplace_get_current_user] = fake_user
    return app


def test_upload_success():
    repo = DummyRepo()
    client = TestClient(_make_app(repo))

    response = client.post(
        "/marketplace/plugins/plugin/artifact",
        files={"file": ("artifact.zip", io.BytesIO(b"zip-data"), "application/zip")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["artifact_path"].startswith("marketplace/plugin/")
    assert repo.last_call is not None
    assert repo.last_call["filename"] == "artifact.zip"


def test_upload_too_large():
    repo = DummyRepo()
    client = TestClient(_make_app(repo))

    big_payload = io.BytesIO(b"a" * (MAX_ARTIFACT_SIZE_BYTES + 1))
    response = client.post(
        "/marketplace/plugins/plugin/artifact",
        files={"file": ("artifact.zip", big_payload, "application/zip")},
    )

    assert response.status_code == 413


def test_upload_storage_unavailable():
    repo = DummyRepo(fail_upload=RuntimeError("no bucket"))
    client = TestClient(_make_app(repo))

    response = client.post(
        "/marketplace/plugins/plugin/artifact",
        files={"file": ("artifact.zip", io.BytesIO(b"zip-data"), "application/zip")},
    )

    assert response.status_code == 503
