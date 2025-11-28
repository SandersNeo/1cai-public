# [NEXUS IDENTITY] ID: 2068138963340429857 | DATE: 2025-11-19

"""
Application service for Authentication module.
"""

import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import jwt
from fastapi import HTTPException, status

from src.infrastructure.logging.structured_logging import StructuredLogger
from src.modules.auth.domain.models import CurrentUser, UserCredentials
from src.modules.auth.infrastructure.config import AuthSettings

logger = StructuredLogger(__name__).logger

DEFAULT_DEMO_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "user_id": "admin-1",
        "roles": ["admin", "moderator"],
        "permissions": ["marketplace:approve", "marketplace:verify"],
        "full_name": "Administrator",
        "email": "admin@example.com",
    },
    {
        "username": "developer",
        "password": "dev123",
        "user_id": "user-1",
        "roles": ["developer"],
        "permissions": ["marketplace:submit", "marketplace:review"],
        "full_name": "Sample Developer",
        "email": "developer@example.com",
    },
]


class AuthService:
    """Service for authenticating users and issuing JWT tokens."""

    def __init__(self, settings: AuthSettings):
        self.settings = settings
        self._users: Dict[str, UserCredentials] = self._load_users()
        self._service_tokens: Dict[str,
                                   CurrentUser] = self._load_service_tokens()

        if self.settings.jwt_secret == "CHANGE_ME":
            logger.warning(
                "JWT_SECRET uses default value. Set a secure secret for production!")

    def _load_users(self) -> Dict[str, UserCredentials]:
        raw_users: List[dict]
        if self.settings.demo_users:
            try:
