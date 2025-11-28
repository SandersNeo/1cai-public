"""
Jira webhook handler for BA Integration.

Handles Jira webhook events:
- Issue status changes
- Issue updates
- Comments added
- Transitions

Updates BA session state based on Jira events.
"""

import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks/jira", tags=["webhooks"])


class JiraWebhookEvent(BaseModel):
    """Jira webhook event model."""

    webhookEvent: str
    issue_event_type_name: Optional[str] = None
    issue: Dict[str, Any]
    changelog: Optional[Dict[str, Any]] = None
    comment: Optional[Dict[str, Any]] = None


class JiraWebhookHandler:
    """
    Handler for Jira webhook events.

    Features:
    - Signature verification
    - Event processing
    - BA session updates
    - Audit logging
    """

    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook handler.

        Args:
            webhook_secret: Secret for signature verification
        """
        self.webhook_secret = webhook_secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Request body
            signature: X-Hub-Signature header value

        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True

        # Calculate expected signature
        expected = hmac.new(
            self.webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(f"sha256={expected}", signature)

    async def handle_issue_updated(self, event: JiraWebhookEvent) -> Dict[str, Any]:
        """
        Handle issue updated event.

        Args:
            event: Webhook event

        Returns:
            Processing result
        """
        issue_key = event.issue.get("key")

        # Extract status change from changelog
        status_change = None
        if event.changelog:
            for item in event.changelog.get("items", []):
                if item.get("field") == "status":
                    status_change = {
                        "from": item.get("fromString"),
                        "to": item.get("toString"),
                    }
                    break

        logger.info("Issue %s updated. Status change: %s")

        # TODO: Update BA session state
        # This would integrate with BA Session Manager to update requirement
        # status

        return {
            "status": "processed",
            "issue_key": issue_key,
            "status_change": status_change,
        }

    async def handle_comment_created(self, event: JiraWebhookEvent) -> Dict[str, Any]:
        """
        Handle comment created event.

        Args:
            event: Webhook event

        Returns:
            Processing result
        """
        issue_key = event.issue.get("key")
        comment = event.comment

        if comment:
            comment.get("body", "")
            comment.get("author", {}).get("displayName", "Unknown")

            logger.info("Comment added to %s by %s")

            # TODO: Notify BA session participants

        return {
            "status": "processed",
            "issue_key": issue_key,
            "comment_added": bool(comment),
        }

    async def process_event(self, event: JiraWebhookEvent) -> Dict[str, Any]:
        """
        Process webhook event.

        Args:
            event: Webhook event

        Returns:
            Processing result
        """
        event_type = event.webhookEvent

        handlers = {
            "jira:issue_updated": self.handle_issue_updated,
            "comment_created": self.handle_comment_created,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(event)
        else:
            logger.warning("Unhandled event type: %s")
            return {"status": "ignored", "event_type": event_type}


# Global handler instance
webhook_handler = JiraWebhookHandler()


@router.post("/events")
async def receive_webhook(
    request: Request, x_hub_signature: Optional[str] = Header(None)
):
    """
    Receive Jira webhook event.

    Args:
        request: FastAPI request
        x_hub_signature: Webhook signature header

    Returns:
        Processing result
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify signature if provided
    if x_hub_signature:
        if not webhook_handler.verify_signature(body, x_hub_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse event
    event_data = await request.json()
    event = JiraWebhookEvent(**event_data)

    # Process event
    result = await webhook_handler.process_event(event)

    return result


@router.get("/health")
async def webhook_health():
    """Webhook endpoint health check."""
    return {
        "status": "healthy",
        "webhook_secret_configured": bool(webhook_handler.webhook_secret),
    }
