# Billing Webhooks Module

## Overview

Stripe webhook handler for billing events.

## Architecture

- **Domain Layer**: Event models
- **Services Layer**: `BillingWebhookHandler`
- **API Layer**: FastAPI webhook endpoint

## Features

- Stripe signature verification
- Subscription lifecycle management
- Payment event handling
- Billing event logging

## Usage

```python
from src.modules.billing_webhooks import router

app.include_router(router)
```
