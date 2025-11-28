"""
Configuration management for BA integrations.

Handles:
- Environment variable loading
- Secrets Manager integration
- BA requirement → Jira issue type mapping
- Issue templates
- Default configurations
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class RequirementPriority(Enum):
    """BA requirement priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequirementType(Enum):
    """BA requirement types."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS = "business"
    TECHNICAL = "technical"


@dataclass
class JiraConfig:
    """Jira integration configuration."""

    base_url: str
    token: str
    project_key: str
    default_priority: str = "Medium"
    default_assignee: Optional[str] = None

    @classmethod
    def from_env(cls) -> "JiraConfig":
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("BA_JIRA_BASE_URL", ""),
            token=os.getenv("BA_JIRA_TOKEN", ""),
            project_key=os.getenv("BA_JIRA_PROJECT_KEY", "BA"),
            default_priority=os.getenv("BA_JIRA_DEFAULT_PRIORITY", "Medium"),
            default_assignee=os.getenv("BA_JIRA_DEFAULT_ASSIGNEE"),
        )

    def is_configured(self) -> bool:
        """Check if Jira is properly configured."""
        return bool(self.base_url and self.token and self.project_key)


@dataclass
class ConfluenceConfig:
    """Confluence integration configuration."""

    base_url: str
    token: str
    space_key: str
    parent_page_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "ConfluenceConfig":
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("BA_CONFLUENCE_BASE_URL", ""),
            token=os.getenv("BA_CONFLUENCE_TOKEN", ""),
            space_key=os.getenv("BA_CONFLUENCE_SPACE_KEY", "BA"),
            parent_page_id=os.getenv("BA_CONFLUENCE_PARENT_PAGE_ID"),
        )

    def is_configured(self) -> bool:
        """Check if Confluence is properly configured."""
        return bool(self.base_url and self.token and self.space_key)


@dataclass
class PowerBIConfig:
    """Power BI integration configuration."""

    client_id: str
    client_secret: str
    tenant_id: str
    workspace_id: str
    dataset_id: str

    @classmethod
    def from_env(cls) -> "PowerBIConfig":
        """Load configuration from environment variables."""
        return cls(
            client_id=os.getenv("BA_POWERBI_CLIENT_ID", ""),
            client_secret=os.getenv("BA_POWERBI_CLIENT_SECRET", ""),
            tenant_id=os.getenv("BA_POWERBI_TENANT_ID", ""),
            workspace_id=os.getenv("BA_POWERBI_WORKSPACE_ID", ""),
            dataset_id=os.getenv("BA_POWERBI_DATASET_ID", ""),
        )

    def is_configured(self) -> bool:
        """Check if Power BI is properly configured."""
        return bool(
            self.client_id
            and self.client_secret
            and self.tenant_id
            and self.workspace_id
            and self.dataset_id
        )


@dataclass
class DataLensConfig:
    """Yandex DataLens integration configuration."""

    api_token: str
    folder_id: str
    dataset_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "DataLensConfig":
        """Load configuration from environment variables."""
        return cls(
            api_token=os.getenv("BA_DATALENS_API_TOKEN", ""),
            folder_id=os.getenv("BA_DATALENS_FOLDER_ID", ""),
            dataset_id=os.getenv("BA_DATALENS_DATASET_ID"),
        )

    def is_configured(self) -> bool:
        """Check if DataLens is properly configured."""
        return bool(self.api_token and self.folder_id)


@dataclass
class OneDocflowConfig:
    """1С:Документооборот integration configuration."""

    base_url: str
    username: str
    password: str

    @classmethod
    def from_env(cls) -> "OneDocflowConfig":
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("BA_1C_DOCFLOW_URL", ""),
            username=os.getenv("BA_1C_DOCFLOW_USERNAME", ""),
            password=os.getenv("BA_1C_DOCFLOW_PASSWORD", ""),
        )

    def is_configured(self) -> bool:
        """Check if 1С:Документооборот is properly configured."""
        return bool(self.base_url and self.username and self.password)


class BAIntegrationConfig:
    """
    Central configuration for all BA integrations.
    """

    def __init__(self):
        self.jira = JiraConfig.from_env()
        self.confluence = ConfluenceConfig.from_env()
        self.powerbi = PowerBIConfig.from_env()
        self.datalens = DataLensConfig.from_env()
        self.onedocflow = OneDocflowConfig.from_env()

        # BA requirement → Jira issue type mapping
        self.requirement_to_issue_type = {
            RequirementType.FUNCTIONAL: "Story",
            RequirementType.NON_FUNCTIONAL: "Task",
            RequirementType.BUSINESS: "Epic",
            RequirementType.TECHNICAL: "Task",
        }

        # Priority mapping
        self.priority_mapping = {
            RequirementPriority.CRITICAL: "Highest",
            RequirementPriority.HIGH: "High",
            RequirementPriority.MEDIUM: "Medium",
            RequirementPriority.LOW: "Low",
        }

    def get_jira_issue_type(self, requirement_type: RequirementType) -> str:
        """Get Jira issue type for BA requirement type."""
        return self.requirement_to_issue_type.get(requirement_type, "Task")

    def get_jira_priority(self, requirement_priority: RequirementPriority) -> str:
        """Get Jira priority for BA requirement priority."""
        return self.priority_mapping.get(requirement_priority, "Medium")

    def get_issue_template(self, requirement_type: RequirementType) -> Dict[str, Any]:
        """
        Get Jira issue template for requirement type.

        Returns:
            Template with default fields
        """
        templates = {
            RequirementType.FUNCTIONAL: {
                "labels": ["ba", "functional", "source:ba"],
                "components": [],
                "description_template": """
## User Story
As a [role], I want [feature] so that [benefit].

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Technical Notes
[Technical implementation details]
                """.strip(),
            },
            RequirementType.BUSINESS: {
                "labels": ["ba", "business", "epic", "source:ba"],
                "components": [],
                "description_template": """
## Business Objective
[Describe the business goal]

## Success Metrics
- Metric 1
- Metric 2

## Scope
[Define scope and boundaries]
                """.strip(),
            },
            RequirementType.NON_FUNCTIONAL: {
                "labels": ["ba", "non-functional", "source:ba"],
                "components": [],
                "description_template": """
## Requirement
[Describe the non-functional requirement]

## Acceptance Criteria
- [ ] Performance: [metric]
- [ ] Security: [requirement]
- [ ] Scalability: [requirement]

## Verification Method
[How to verify this requirement]
                """.strip(),
            },
            RequirementType.TECHNICAL: {
                "labels": ["ba", "technical", "source:ba"],
                "components": [],
                "description_template": """
## Technical Requirement
[Describe the technical requirement]

## Implementation Approach
[Proposed technical solution]

## Dependencies
- Dependency 1
- Dependency 2
                """.strip(),
            },
        }

        return templates.get(requirement_type, templates[RequirementType.FUNCTIONAL])

    def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate all integration configurations.

        Returns:
            Dictionary with configuration status for each integration
        """
        return {
            "jira": self.jira.is_configured(),
            "confluence": self.confluence.is_configured(),
            "powerbi": self.powerbi.is_configured(),
            "datalens": self.datalens.is_configured(),
            "onedocflow": self.onedocflow.is_configured(),
        }

    def get_configured_integrations(self) -> list[str]:
        """Get list of properly configured integrations."""
        validation = self.validate_configuration()
        return [name for name, configured in validation.items() if configured]


# Global configuration instance
config = BAIntegrationConfig()
