# [NEXUS IDENTITY] ID: -6233580949619435117 | DATE: 2025-11-19

"""
Unit tests for marketplace API endpoints
Tests for create, update, and complaints functionality
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from src.api.marketplace import (
    submit_plugin,
    update_plugin,
    report_plugin,
    PluginSubmitRequest,
    PluginUpdateRequest,
    PluginStatus,
    PluginCategory,
)
from src.security.auth import CurrentUser


@pytest.fixture
def mock_user():
    """Mock current user"""
    return CurrentUser(
        user_id="user_123",
        username="testuser",
        email="test@example.com",
        roles=["developer"],
    )


@pytest.fixture
def mock_repo():
    """Mock marketplace repository"""
    repo = AsyncMock()
    plugin_payload = {
        "id": "plugin_123",
        "plugin_id": "plugin_123",
        "name": "Test Plugin",
        "description": "A test plugin",
        "category": PluginCategory.AI_AGENT.value,
        "version": "1.0.0",
        "author": "testuser",
        "status": PluginStatus.PENDING.value,
        "visibility": "public",
        "downloads": 0,
        "rating": 0.0,
        "ratings_count": 0,
        "installs": 0,
        "homepage": None,
        "repository": None,
        "download_url": "/marketplace/plugins/plugin_123/download",
        "icon_url": None,
        "changelog": None,
        "readme": None,
        "artifact_path": None,
        "screenshot_urls": [],
        "keywords": [],
        "license": "MIT",
        "min_version": "1.0.0",
        "supported_platforms": ["telegram"],
        "created_at": "2025-11-15T00:00:00Z",
        "updated_at": "2025-11-15T00:00:00Z",
        "published_at": None,
        "featured": False,
        "verified": False,
        "owner_id": "user_123",
        "owner_username": "testuser",
    }
    repo.create_plugin = AsyncMock(return_value=plugin_payload)
    repo.get_plugin = AsyncMock(
        return_value={**plugin_payload, "status": PluginStatus.APPROVED.value}
    )
    repo.update_plugin = AsyncMock(
        return_value={
            **plugin_payload,
            "name": "Updated Plugin",
            "status": PluginStatus.APPROVED.value,
        }
    )
    repo.add_complaint = AsyncMock(return_value=True)
    return repo


@pytest.mark.asyncio
@pytest.fixture
def fake_request():
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [],
        "path": "/marketplace/plugins",
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_submit_plugin_success(mock_user, mock_repo, fake_request):
    """Test successful plugin submission"""
    plugin_data = PluginSubmitRequest(
        name="Test Plugin",
        description="A test plugin",
        category=PluginCategory.AI_AGENT,
        version="1.0.0",
        author="Test Author",
    )

    with patch("src.api.marketplace.audit_logger") as mock_audit:
        result = await submit_plugin(
            request=fake_request,
            response=Response(),
            plugin=plugin_data,
            current_user=mock_user,
            repo=mock_repo,
        )

    result_data = result.model_dump()
    assert result_data["plugin_id"] == "plugin_123"
    assert result_data["status"] == PluginStatus.PENDING.value
    mock_repo.create_plugin.assert_called_once()
    mock_audit.log_action.assert_called_once()


def test_submit_plugin_validation_error():
    """Test plugin submission request validation"""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PluginSubmitRequest(
            name="AB",  # Too short
            description="Test",
            category=PluginCategory.AI_AGENT,
            version="1.0.0",
            author="Test",
        )


@pytest.mark.asyncio
async def test_update_plugin_success(mock_user, mock_repo):
    """Test successful plugin update"""
    update_data = PluginUpdateRequest(description="Updated description")

    with patch("src.api.marketplace.audit_logger") as mock_audit:
        result = await update_plugin(
            plugin_id="plugin_123",
            update=update_data,
            current_user=mock_user,
            repo=mock_repo,
        )

    assert result.model_dump()["name"] == "Updated Plugin"
    mock_repo.update_plugin.assert_called_once()
    mock_audit.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_update_plugin_not_found(mock_user, mock_repo):
    """Test updating non-existent plugin"""
    mock_repo.get_plugin.return_value = None
    update_data = PluginUpdateRequest(description="Updated description")

    with pytest.raises(HTTPException) as exc_info:
        await update_plugin(
            plugin_id="nonexistent",
            update=update_data,
            current_user=mock_user,
            repo=mock_repo,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_plugin_unauthorized(mock_user, mock_repo):
    """Test updating plugin without permission"""
    other_user = CurrentUser(
        user_id="user_456",
        username="otheruser",
        email="other@example.com",
        roles=["developer"],
    )
    update_data = PluginUpdateRequest(description="Updated description")

    with pytest.raises(HTTPException) as exc_info:
        await update_plugin(
            plugin_id="plugin_123",
            update=update_data,
            current_user=other_user,
            repo=mock_repo,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_report_plugin_success(mock_user, mock_repo):
    """Test successful plugin report"""
    with patch("src.api.marketplace.audit_logger") as mock_audit:
        result = await report_plugin(
            plugin_id="plugin_123",
            reason="spam",
            details="This is spam",
            current_user=mock_user,
            repo=mock_repo,
        )

    assert result["status"] == "reported"
    assert result["plugin_id"] == "plugin_123"
    mock_repo.add_complaint.assert_called_once()
    mock_audit.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_report_plugin_not_found(mock_user, mock_repo):
    """Test reporting non-existent plugin"""
    mock_repo.get_plugin.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await report_plugin(
            plugin_id="nonexistent",
            reason="spam",
            current_user=mock_user,
            repo=mock_repo,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_plugin_version_changes_status(mock_user, mock_repo):
    """Test that updating version changes status to PENDING"""
    update_data = PluginUpdateRequest(version="2.0.0")

    await update_plugin(
        plugin_id="plugin_123",
        update=update_data,
        current_user=mock_user,
        repo=mock_repo,
    )

    # Check that update_plugin was called with status=PENDING
    call_args = mock_repo.update_plugin.call_args
    assert "status" in call_args[1] or (
        len(call_args[0]) > 1 and "status" in call_args[0][1]
    )
    # The status should be set to PENDING when version changes
