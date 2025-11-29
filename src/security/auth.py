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
    """Класс TokenResponse.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCredentials(BaseModel):
    """Класс UserCredentials.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    username: str
    password: str
    user_id: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    full_name: Optional[str] = None
    email: Optional[str] = None


class CurrentUser(BaseModel):
    """Класс CurrentUser.
    
    TODO: Добавить описание класса.
    
    Attributes:
        TODO: Описать атрибуты класса.
    """
    user_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    full_name: Optional[str] = None
    email: Optional[str] = None

    def has_role(self, *required_roles: str) -> bool:
        """TODO: Описать функцию has_role.
        
        Returns:
            TODO: Описать возвращаемое значение.
        """
        return any(role in self.roles for role in required_roles)

    def has_permission(self, *required_permissions: str) -> bool:
        """TODO: Описать функцию has_permission.
        
        Returns:
            TODO: Описать возвращаемое значение.
        """
        return any(
            permission in self.permissions for permission in required_permissions
        )


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
        """TODO: Описать функцию __init__.
        
        Args:
            settings: TODO: Описать параметр.
        """
        self.settings = settings
        self._users: Dict[str, UserCredentials] = self._load_users()
        self._service_tokens: Dict[str, CurrentUser] = self._load_service_tokens()

        if self.settings.jwt_secret == "CHANGE_ME":
            logger.warning(
                "JWT_SECRET uses default value. Set a secure secret for production!"
            )

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
                logger.info(
                    "Using default demo users. Configure AUTH_DEMO_USERS for production."
                )
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
        """TODO: Описать функцию authenticate_user.
        
        Args:
            username: TODO: Описать параметр.
            password: TODO: Описать параметр.
        
        Returns:
            TODO: Описать возвращаемое значение.
        """
        user = self._users.get(username)
        if not user:
            return None
        if not secrets.compare_digest(password, user.password):
            return None
        return user

    def create_access_token(
        self, user: UserCredentials, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token with best practices

        Features:
        - Short expiration time (default 60 minutes)
        - UTC timestamps
        - Minimal payload (security best practice)
        - Secure algorithm (HS256)
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)

        now = datetime.now(timezone.utc)
        payload = {
            "sub": user.user_id,  # Subject (user ID)
            "username": user.username,
            "roles": user.roles,
            "permissions": user.permissions,
            "full_name": user.full_name,
            "email": user.email,
            "iat": int(now.timestamp()),  # Issued at (Unix timestamp)
            "exp": int(
                (now + expires_delta).timestamp()
            ),  # Expiration (Unix timestamp)
            "type": "access",  # Token type for clarity
        }

        # Best practice: Use secure secret and algorithm
        token = jwt.encode(
            payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm
        )
        return token

    def create_refresh_token(self, user: UserCredentials) -> str:
        """
        Create refresh token for token renewal

        Best practice: Longer expiration (7-30 days) for refresh tokens
        """
        expires_delta = timedelta(days=7)  # Refresh tokens last 7 days
        now = datetime.now(timezone.utc)

        payload = {
            "sub": user.user_id,
            "username": user.username,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
            "type": "refresh",  # Different type for refresh tokens
        }

        # Use same secret but different type
        token = jwt.encode(
            payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm
        )
        return token

    def decode_token(self, token: str, token_type: str = "access") -> CurrentUser:
        """
        Decode and validate JWT token with best practices

        Features:
        - Token expiration validation
        - Token type validation
        - Payload validation
        - Secure error handling (don't leak sensitive info)
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                },
            )
        except jwt.ExpiredSignatureError as exc:
            logger.warning(
                "JWT expired",
                extra={"error_type": "ExpiredSignatureError", "token_type": token_type},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Please refresh your token.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except jwt.InvalidTokenError as exc:
            logger.warning(
                "JWT invalid",
                extra={"error_type": "InvalidTokenError", "token_type": token_type},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token. Please authenticate again.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except jwt.PyJWTError as exc:
            logger.warning(
                "JWT decode error",
                extra={"error_type": type(exc).__name__, "token_type": token_type},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        # Validate token type
        if payload.get("type") != token_type:
            logger.warning(
                "Invalid token type",
                extra={"expected_type": token_type, "actual_type": payload.get("type")},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate required fields
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
        """TODO: Описать функцию authenticate_service_token.
        
        Args:
            token: TODO: Описать параметр.
        
        Returns:
            TODO: Описать возвращаемое значение.
        """
        if not token:
            return None
        principal = self._service_tokens.get(token)
        if principal:
            return principal
        return None


@lru_cache()
def get_auth_settings() -> AuthSettings:
    """TODO: Описать функцию get_auth_settings.
    
    Returns:
        TODO: Описать возвращаемое значение.
    """
    return AuthSettings()


@lru_cache()
def get_auth_service() -> AuthService:
    """TODO: Описать функцию get_auth_service.
    
    Returns:
        TODO: Описать возвращаемое значение.
    """
    return AuthService(get_auth_settings())


async def get_current_user(
    request: Request, token: Optional[str] = Depends(oauth2_scheme)
) -> CurrentUser:
    """TODO: Описать функцию get_current_user.
    
    Args:
        request: TODO: Описать параметр.
        token: TODO: Описать параметр.
    
    Returns:
        TODO: Описать возвращаемое значение.
    """
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
    """TODO: Описать функцию require_roles."""
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        """TODO: Описать функцию dependency.
        
        Args:
            user: TODO: Описать параметр.
        
        Returns:
            TODO: Описать возвращаемое значение.
        """
        if roles and not user.has_role(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return user

    return dependency


def require_permissions(*permissions: str):
    """TODO: Описать функцию require_permissions."""
    async def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        """TODO: Описать функцию dependency.
        
        Args:
            user: TODO: Описать параметр.
        
        Returns:
            TODO: Описать возвращаемое значение.
        """
        if permissions and not user.has_permission(*permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
