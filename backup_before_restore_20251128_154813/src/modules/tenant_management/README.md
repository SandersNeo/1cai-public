# Tenant Management Module

## Overview

Tenant registration, billing, and usage tracking.

## Architecture

- **Domain Layer**: Pydantic models for registration
- **Services Layer**: `TenantManagementService` with Stripe integration
- **API Layer**: FastAPI endpoints

## Features

- Self-serve tenant registration
- 14-day trial period
- Stripe subscription management
- Usage tracking and limits
- Multi-tenant resource isolation

## Usage

```python
from src.modules.tenant_management import router

app.include_router(router)
```
