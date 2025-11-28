# [NEXUS IDENTITY] ID: 2068138963340429857 | DATE: 2025-11-19

"""
JWT-based authentication utilities.
Версия: 2.1.0

Улучшения:
- Structured logging
- Улучшена обработка ошибок
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.security.roles import enrich_user_from_db
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


class AuthSettings(BaseSettings):
    """Authentication configuration (loaded from environment variables)."""

    jwt_secret: str = Field(default="CHANGE_ME")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    demo_users: Optional[str] = Field(default=None)
    service_tokens: Optional[str] = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCredentials(BaseModel):
    username: str
    password: str
    user_id: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    full_name: Optional[str] = None
    email: Optional[str] = None


class CurrentUser(BaseModel):
    user_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    full_name: Optional[str] = None
    email: Optional[str] = None

    def has_role(self, *required_roles: str) -> bool:
        return any(role in self.roles for role in required_roles)

    def has_permission(self, *required_permissions: str) -> bool:
        return any(
            permission in self.permissions for permission in required_permissions)


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
                "JWT_SECRET uses default value. Set a secure secret for production!"
            )

    def _load_users(self) -> Dict[str, UserCredentials]:
        raw_users: List[dict]
        if self.settings.demo_users:
            try:
