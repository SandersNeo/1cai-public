"""JWT-based authentication utilities."""
from __future__ import annotations

import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from src.security.audit import AuditLogger, get_audit_logger
from src.security.roles import enrich_user_from_db

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


class AuthSettings(BaseSettings):
    """Authentication configuration (loaded from environment variables)."""

    jwt_secret: str = Field(default="CHANGE_ME", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    demo_users: Optional[str] = Field(default=None, env="AUTH_DEMO_USERS")
    service_tokens: Optional[str] = Field(default=None, env="SERVICE_API_TOKENS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
        return any(permission in self.permissions for permission in required_permissions)


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
        self._service_tokens: Dict[str, CurrentUser] = self._load_service_tokens()

        if self.settings.jwt_secret == "CHANGE_ME":
            logger.warning("JWT_SECRET uses default value. Set a secure secret for production!")

    def _load_users(self) -> Dict[str, UserCredentials]:
        raw_users: List[dict]
        if self.settings.demo_users:
            try:
                raw_users = json.loads(self.settings.demo_users)
            except json.JSONDecodeError as exc:
                logger.error("Failed to parse AUTH_DEMO_USERS JSON: %s", exc)
                raw_users = DEFAULT_DEMO_USERS
        else:
            if os.getenv("AUTH_DEMO_USERS") is None:
                logger.info("Using default demo users. Configure AUTH_DEMO_USERS for production.")
            raw_users = DEFAULT_DEMO_USERS

        users: Dict[str, UserCredentials] = {}
        for entry in raw_users:
            try:
                user = UserCredentials(**entry)
            except Exception as exc:  # noqa: BLE001
                logger.error("Invalid user entry skipped: %s", exc)
                continue
            users[user.username] = user
        return users

    def _load_service_tokens(self) -> Dict[str, CurrentUser]:
        if not self.settings.service_tokens:
            return {}

        try:
            data = json.loads(self.settings.service_tokens)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse SERVICE_API_TOKENS JSON: %s", exc)
            return {}

        token_map: Dict[str, CurrentUser] = {}

        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = []
            for name, values in data.items():
                if isinstance(values, dict):
                    values.setdefault("name", name)
                    entries.append(values)
        else:
            logger.error("SERVICE_API_TOKENS must be dict or list")
            return {}

        for entry in entries:
            try:
                token_value = entry.get("token")
                name = entry.get("name") or entry.get("service")
                if not token_value or not name:
                    raise ValueError("Missing name or token")
                roles = entry.get("roles") or ["service"]
                permissions = entry.get("permissions") or []
                principal = CurrentUser(
                    user_id=f"service:{name}",
                    username=name,
                    roles=roles,
                    permissions=permissions,
                    full_name=entry.get("description"),
                    email=None,
                )
                token_map[token_value] = principal
            except Exception as exc:  # noqa: BLE001
                logger.error("Invalid service token configuration skipped: %s", exc)
        if token_map and self.settings.service_tokens:
            logger.info("Loaded %d service API tokens", len(token_map))
        return token_map

    def authenticate_user(self, username: str, password: str) -> Optional[UserCredentials]:
        user = self._users.get(username)
        if not user:
            return None
        if not secrets.compare_digest(password, user.password):
            return None
        return user

    def create_access_token(self, user: UserCredentials, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)

        now = datetime.utcnow()
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "roles": user.roles,
            "permissions": user.permissions,
            "full_name": user.full_name,
            "email": user.email,
            "iat": now,
            "exp": now + expires_delta,
        }

        token = jwt.encode(payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)
        return token

    def decode_token(self, token: str) -> CurrentUser:
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            logger.warning("JWT expired: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except jwt.PyJWTError as exc:
            logger.warning("JWT decode error: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        user_id = payload.get("sub")
        username = payload.get("username")
        if not user_id or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return CurrentUser(
            user_id=user_id,
            username=username,
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            full_name=payload.get("full_name"),
            email=payload.get("email"),
        )

    def authenticate_service_token(self, token: str) -> Optional[CurrentUser]:
        if not token:
            return None
        principal = self._service_tokens.get(token)
        if principal:
            return principal
        return None


@lru_cache()
def get_auth_settings() -> AuthSettings:
    return AuthSettings()


@lru_cache()
def get_auth_service() -> AuthService:
    return AuthService(get_auth_settings())


async def get_current_user(request: Request, token: Optional[str] = Depends(oauth2_scheme)) -> CurrentUser:
    auth_service = get_auth_service()

    if token:
        principal = auth_service.decode_token(token)
        return await enrich_user_from_db(principal)

    service_token = request.headers.get("X-Service-Token")
    if service_token:
        service_user = auth_service.authenticate_service_token(service_token)
        if service_user:
            return service_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token",
        )

    current = getattr(request.state, "current_user", None)
    if current:
        return await enrich_user_from_db(current)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_roles(*roles: str):
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if roles and not user.has_role(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return user

    return dependency


def require_permissions(*permissions: str):
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if permissions and not user.has_permission(*permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


