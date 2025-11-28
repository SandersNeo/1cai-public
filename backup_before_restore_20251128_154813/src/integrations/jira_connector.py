"""
Enhanced Jira connector for BA Integration.

Extends the base Jira client with BA-specific functionality:
- BA requirement → Jira issue mapping
- Epic/Story/Subtask creation with templates
- Webhook handling for status changes
- DLQ for failed operations
- Comprehensive audit logging
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .base_client import BaseIntegrationClient
from .exceptions import IntegrationConfigError

logger = logging.getLogger(__name__)


class JiraIssueType(Enum):
    """Jira issue types."""
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    SUBTASK = "Sub-task"
    BUG = "Bug"


class JiraStatus(Enum):
    """Common Jira statuses."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    BLOCKED = "Blocked"


class JiraConnector(BaseIntegrationClient):
    """
    Enhanced Jira client for BA Integration.

    Features:
    - Create/update issues (Epic, Story, Subtask)
    - BA requirement mapping
    - Template-based issue creation
    - Webhook handling
    - Search and filtering
    - Audit logging
    """

    ISSUE_ENDPOINT = "/rest/api/3/issue"
    SEARCH_ENDPOINT = "/rest/api/3/search"

    # BA-specific labels
    BA_SOURCE_LABEL = "source:ba"

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        project_key: str,
        transport: Optional[Any] = None,
    ) -> None:
        """
        Initialize Jira connector.

        Args:
            base_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
            token: API token or OAuth token
            project_key: Default project key for BA issues
            transport: Optional HTTP transport
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        super().__init__(base_url=base_url, headers=headers, transport=transport)
        self.project_key = project_key

        # DLQ for failed operations
        self.dlq: List[Dict[str, Any]] = []

    @classmethod
    def from_env(cls, *, transport: Optional[Any] = None) -> "JiraConnector":
        """Create connector from environment variables."""
        base_url = os.getenv("BA_JIRA_BASE_URL")
        token = os.getenv("BA_JIRA_TOKEN")
        project_key = os.getenv("BA_JIRA_PROJECT_KEY", "BA")

        if not base_url or not token:
            raise IntegrationConfigError(
                "BA_JIRA_BASE_URL and BA_JIRA_TOKEN must be configured."
            )
        return cls(
            base_url=base_url,
            token=token,
            project_key=project_key,
            transport=transport
        )

    async def create_epic_from_requirement(
        self,
        *,
        requirement_id: str,
        title: str,
        description: str,
        priority: str = "Medium",
        labels: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create Epic from BA requirement.

        Args:
            requirement_id: BA requirement ID
            title: Epic title
            description: Epic description
            priority: Priority (Highest, High, Medium, Low, Lowest)
            labels: Additional labels
            custom_fields: Custom field values

        Returns:
            Created epic data
        """
        all_labels = [self.BA_SOURCE_LABEL, f"req:{requirement_id}"]
        if labels:
            all_labels.extend(labels)

        fields = {
            "project": {"key": self.project_key},
            "summary": title,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            },
            "issuetype": {"name": JiraIssueType.EPIC.value},
            "priority": {"name": priority},
            "labels": all_labels,
        }

        # Add custom fields
        if custom_fields:
            fields.update(custom_fields)

        try:
