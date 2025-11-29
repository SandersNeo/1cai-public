import os

from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from src.modules.billing_webhooks.services.webhook_handler import BillingWebhookHandler

router = APIRouter(tags=["Billing Webhooks"])


def get_db_pool() -> Any:
    """DB pool dependency."""
    from src.database import get_pool

    return get_pool()


@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="Stripe-Signature")) -> Dict[str, Any]:
    """Stripe webhook endpoint."""
    payload = await request.body()

    # Parse event
    try:
        import stripe

        event = stripe.Webhook.construct_event(
            payload, stripe_signature, os.getenv("STRIPE_WEBHOOK_SECRET", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event
    handler = BillingWebhookHandler(get_db_pool())
    result = await handler.handle_event(event)

    return result
