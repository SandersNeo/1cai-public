import hashlib
import os
import secrets
import string
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

import asyncpg

from src.modules.tenant_management.domain.models import \
    TenantRegistrationRequest
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class TenantManagementService:
    """Service for tenant management."""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

        # Stripe (if available)
        self.stripe_available = False
        try:
