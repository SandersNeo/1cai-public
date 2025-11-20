# [NEXUS IDENTITY] ID: 5039146811883525688 | DATE: 2025-11-19

"""
E2E tests for marketplace API with authentication and role-based access.
These tests rely on dependency overrides so we can exercise the FastAPI router
without real JWT tokens or a Postgres marketplace repository.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.api.marketplace import get_marketplace_repository
from src.security.auth import CurrentUser, get_current_user


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def developer_user():
    return CurrentUser(
        user_id="dev_123",
        username="developer",
        email="dev@example.com",
        roles=["developer"],
    )


@pytest.fixture
def regular_user():
    return CurrentUser(
        user_id="user_123",
        username="user",
        email="user@example.com",
        roles=["user"],
    )


class DummyMarketplaceRepo:
    """Simple in-memory marketplace repository for integration tests."""

    def __init__(self):
        self.plugins = {}
        self.complaints = []

    async def create_plugin(
        self, plugin_id, owner_id, owner_username, payload, download_url
    ):
        plugin = {
            "id": plugin_id,
            "plugin_id": plugin_id,
            "name": payload["name"],
            "description": payload["description"],
            "category": payload["category"],
            "version": payload["version"],
            "author": payload.get("author", owner_username),
            "status": payload.get("status", "pending"),
            "visibility": payload.get("visibility", "public"),
            "downloads": 0,
            "rating": 0.0,
            "ratings_count": 0,
            "installs": 0,
            "homepage": payload.get("homepage"),
            "repository": payload.get("repository"),
            "download_url": download_url,
            "icon_url": payload.get("icon_url"),
            "screenshot_urls": payload.get("screenshot_urls", []),
            "keywords": payload.get("keywords", []),
            "license": payload.get("license", "MIT"),
            "min_version": payload.get("min_version", "1.0.0"),
            "supported_platforms": payload.get("supported_platforms", []),
            "readme": payload.get("readme"),
            "changelog": payload.get("changelog"),
            "artifact_path": payload.get("artifact_path"),
            "created_at": "2025-11-15T00:00:00Z",
            "updated_at": "2025-11-15T00:00:00Z",
            "published_at": None,
            "featured": False,
            "verified": False,
            "owner_id": owner_id,
            "owner_username": owner_username,
        }
        self.plugins[plugin_id] = plugin
        return plugin

    async def get_plugin(self, plugin_id):
        return self.plugins.get(plugin_id)

    async def update_plugin(self, plugin_id, update_data):
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return None
        plugin.update(update_data)
        plugin["updated_at"] = "2025-11-15T00:00:01Z"
        return plugin

    async def add_complaint(
        self, complaint_id, plugin_id, user_id, reason, details=None
    ):
        if plugin_id not in self.plugins:
            return False
        self.complaints.append(
            {
                "complaint_id": complaint_id,
                "plugin_id": plugin_id,
                "user_id": user_id,
                "reason": reason,
                "details": details,
            }
        )
        return True

    def seed_plugin(self, plugin_id: str):
        if plugin_id not in self.plugins:
            self.plugins[plugin_id] = {
                "id": plugin_id,
                "plugin_id": plugin_id,
                "name": "Seed Plugin",
                "description": "Seed",
                "category": "ai_agent",
                "version": "1.0.0",
                "author": "seed",
                "status": "approved",
                "visibility": "public",
                "downloads": 0,
                "rating": 0.0,
                "ratings_count": 0,
                "installs": 0,
                "homepage": None,
                "repository": None,
                "download_url": f"/marketplace/plugins/{plugin_id}/download",
                "icon_url": None,
                "screenshot_urls": [],
                "keywords": [],
                "license": "MIT",
                "min_version": "1.0.0",
                "supported_platforms": [],
                "readme": None,
                "changelog": None,
                "artifact_path": None,
                "created_at": "2025-11-15T00:00:00Z",
                "updated_at": "2025-11-15T00:00:00Z",
                "published_at": None,
                "featured": False,
                "verified": False,
                "owner_id": "seed_user",
                "owner_username": "seed",
            }


def _override_repo(repo: DummyMarketplaceRepo):
    app.dependency_overrides[get_marketplace_repository] = lambda: repo


def _override_current_user(user: CurrentUser):
    app.dependency_overrides[get_current_user] = lambda: user


@pytest.mark.asyncio
async def test_submit_plugin_requires_developer_role(client, developer_user):
    repo = DummyMarketplaceRepo()
    _override_repo(repo)
    _override_current_user(developer_user)

    response = client.post(
        "/marketplace/plugins",
        json={
            "name": "Test Plugin",
            "description": "A test plugin for E2E testing",
            "category": "ai_agent",
            "version": "1.0.0",
            "author": "Test Author",
        },
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "plugin_id" in data
    assert data["status"] == "pending"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_plugin_rejects_regular_user(client, regular_user):
    repo = DummyMarketplaceRepo()
    _override_repo(repo)
    _override_current_user(regular_user)

    response = client.post(
        "/marketplace/plugins",
        json={
            "name": "Test Plugin",
            "description": "A test plugin",
            "category": "ai_agent",
            "version": "1.0.0",
            "author": "Test Author",
        },
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_plugin_requires_ownership(client, developer_user):
    repo = DummyMarketplaceRepo()
    _override_repo(repo)
    _override_current_user(developer_user)

    create_response = client.post(
        "/marketplace/plugins",
        json={
            "name": "My Plugin",
            "description": "My plugin description",
            "category": "ai_agent",
            "version": "1.0.0",
            "author": "Me",
        },
        headers={"Authorization": "Bearer test_token"},
    )

    assert create_response.status_code == 201
    plugin_id = create_response.json()["plugin_id"]

    update_response = client.put(
        f"/marketplace/plugins/{plugin_id}",
        json={"description": "Updated description"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert update_response.status_code == 200
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_report_plugin_creates_complaint(client, regular_user):
    repo = DummyMarketplaceRepo()
    repo.seed_plugin("test_plugin_123")
    _override_repo(repo)
    _override_current_user(regular_user)

    response = client.post(
        "/marketplace/plugins/test_plugin_123/report",
        params={"reason": "spam", "details": "This is spam"},
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reported"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_marketplace_authorization_flow(client, developer_user, regular_user):
    repo = DummyMarketplaceRepo()
    _override_repo(repo)

    current = {"user": developer_user}
    app.dependency_overrides[get_current_user] = lambda: current["user"]

    submit_response = client.post(
        "/marketplace/plugins",
        json={
            "name": "Auth Test Plugin",
            "description": "Testing auth",
            "category": "ai_agent",
            "version": "1.0.0",
            "author": "Test",
        },
        headers={"Authorization": "Bearer dev_token"},
    )
    assert submit_response.status_code == 201

    current["user"] = regular_user
    forbidden_response = client.post(
        "/marketplace/plugins",
        json={
            "name": "Auth Fail Plugin",
            "description": "Testing auth fail",
            "category": "ai_agent",
            "version": "1.0.0",
            "author": "Test",
        },
        headers={"Authorization": "Bearer user_token"},
    )
    assert forbidden_response.status_code == 403

    app.dependency_overrides.clear()
