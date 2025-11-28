"""
Webhook Handler Service
Processes GitHub webhook events
"""
from typing import Any, Dict

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.github_integration.domain.models import PullRequestEvent

logger = StructuredLogger(__name__).logger


class WebhookHandler:
    """Handles GitHub webhook events"""

    async def handle_pull_request_event(
            self, event_data: Dict[str, Any]) -> PullRequestEvent:
        """
        Process Pull Request webhook event

        Args:
            event_data: Raw webhook payload

        Returns:
            Validated PullRequestEvent object

        Raises:
            ValueError: If event data is invalid
        """
        # Input validation
        if not isinstance(event_data, dict):
            logger.warning(
                "Invalid event_data type",
                extra={"event_data_type": type(event_data).__name__},
            )
            raise ValueError("Invalid event data format")

        # Extract required fields
        action = event_data.get("action")
        if not action:
            raise ValueError("Missing 'action' field in event data")

        pr_data = event_data.get("pull_request", {})
        if not pr_data:
            raise ValueError("Missing 'pull_request' field in event data")

        repo_data = event_data.get("repository", {})
        if not repo_data:
            raise ValueError("Missing 'repository' field in event data")

        sender_data = event_data.get("sender", {})

        # Build PullRequestEvent (Pydantic will validate)
        try:
