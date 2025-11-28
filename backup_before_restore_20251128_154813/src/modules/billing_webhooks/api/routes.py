import os

from fastapi import APIRouter, Header, HTTPException, Request

from src.modules.billing_webhooks.services.webhook_handler import \
    BillingWebhookHandler

router = APIRouter(tags=["Billing Webhooks"])


def get_db_pool():
    """DB pool dependency."""
    from src.database import get_pool

    return get_pool()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(
        None,
        alias="Stripe-Signature")):
    """Stripe webhook endpoint."""
    payload = await request.body()

    # Parse event
    try:

        # Handle event
    handler = BillingWebhookHandler(get_db_pool())
    result = await handler.handle_event(event)

    return result
