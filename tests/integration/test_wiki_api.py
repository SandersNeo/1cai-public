from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.wiki import get_wiki_service
from src.main import app
from src.services.wiki.models import WikiPage
from src.services.wiki.service import WikiService

# Mock Data
MOCK_PAGE_ID = "test-page-id"
MOCK_SLUG = "test-slug"
MOCK_TITLE = "Test Page"
MOCK_CONTENT = "# Test Content"
MOCK_HTML = "<h1>Test Content</h1>"


@pytest.fixture
def mock_wiki_service():
    service = AsyncMock(spec=WikiService)

    # Setup get_page
    service.get_page.return_value = WikiPage(
        id=MOCK_PAGE_ID,
        slug=MOCK_SLUG,
        namespace="default",
        title=MOCK_TITLE,
        current_revision_id="rev-1",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        html_content=None,
    )

    # Setup create_page
    service.create_page.return_value = WikiPage(
        id=MOCK_PAGE_ID,
        slug=MOCK_SLUG,
        namespace="default",
        title=MOCK_TITLE,
        current_revision_id="rev-1",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Setup update_page
    service.update_page.return_value = WikiPage(
        id=MOCK_PAGE_ID,
        slug=MOCK_SLUG,
        namespace="default",
        title="Updated Title",
        current_revision_id="rev-2",
        version=2,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Setup list_pages (NEW)
    service.list_pages.return_value = [
        WikiPage(
            id=MOCK_PAGE_ID,
            slug=MOCK_SLUG,
            namespace="default",
            title=MOCK_TITLE,
            current_revision_id="rev-1",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    ]

    # Setup render
    service.render_content.return_value = MOCK_HTML

    return service


@pytest.fixture
def client(mock_wiki_service):
    app.dependency_overrides[get_wiki_service] = lambda: mock_wiki_service
    return TestClient(app)


def test_get_page(client, mock_wiki_service):
    response = client.get(f"/api/v1/wiki/pages/{MOCK_SLUG}")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == MOCK_SLUG
    assert data["title"] == MOCK_TITLE
    mock_wiki_service.get_page.assert_called_with(MOCK_SLUG, None)


def test_get_page_not_found(client, mock_wiki_service):
    mock_wiki_service.get_page.return_value = None
    response = client.get("/api/v1/wiki/pages/unknown")
    assert response.status_code == 404


def test_list_pages(client, mock_wiki_service):
    """Test the new list pages endpoint"""
    response = client.get("/api/v1/wiki/pages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["slug"] == MOCK_SLUG
    mock_wiki_service.list_pages.assert_called_with(50, 0)


def test_create_page(client, mock_wiki_service):
    payload = {
        "slug": "new-page",
        "title": "New Page",
        "content": "Content",
        "namespace": "default",
        "commit_message": "Init",
    }
    response = client.post("/api/v1/wiki/pages", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == MOCK_PAGE_ID
    mock_wiki_service.create_page.assert_called()


def test_update_page_success(client, mock_wiki_service):
    payload = {"content": "New Content", "version": 1, "commit_message": "Update"}
    response = client.put(f"/api/v1/wiki/pages/{MOCK_SLUG}", json=payload)
    assert response.status_code == 200
    assert response.json()["version"] == 2


def test_update_page_conflict(client, mock_wiki_service):
    # Simulate conflict exception
    mock_wiki_service.update_page.side_effect = ValueError(
        "Conflict: Page has been modified"
    )

    payload = {"content": "New Content", "version": 1, "commit_message": "Update"}
    response = client.put(f"/api/v1/wiki/pages/{MOCK_SLUG}", json=payload)
    assert response.status_code == 409
    # Check against the structured error response format
    error_data = response.json()
    assert "error" in error_data
    assert "Conflict" in error_data["error"]["message"]


def test_preview_content(client, mock_wiki_service):
    response = client.post("/api/v1/wiki/preview", params={"content": "# Hello"})
    assert response.status_code == 200
    assert response.json()["html"] == MOCK_HTML
    mock_wiki_service.render_content.assert_called_with("# Hello")
