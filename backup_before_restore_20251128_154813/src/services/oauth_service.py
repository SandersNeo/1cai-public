# [NEXUS IDENTITY] ID: 3863840099083275034 | DATE: 2025-11-22

"""
OAuth Service для 1C AI Stack
==============================

Реализация OAuth2 Authorization Code flow с PKCE для внешних интеграций.

Поддерживаемые провайдеры:
- GitHub
- GitLab
- Jira (Atlassian)
- Confluence (Atlassian)

Версия: 1.0.0
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urlencode

import asyncpg
import httpx
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class OAuthService:
    """Сервис для работы с OAuth2 аутентификацией"""

    def __init__(self):
        """Инициализация OAuth сервиса"""
        # Ключ шифрования токенов
        encryption_key = os.getenv("OAUTH_ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError(
                "OAUTH_ENCRYPTION_KEY не установлен в переменных окружения")

        self.fernet = Fernet(encryption_key.encode())

        # Конфигурация провайдеров
        self.providers = {
            "github": {
                "name": "GitHub",
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_url": "https://api.github.com/user",
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "redirect_uri": os.getenv("GITHUB_REDIRECT_URI"),
                "scope": "repo read:user",
            },
            "gitlab": {
                "name": "GitLab",
                "auth_url": "https://gitlab.com/oauth/authorize",
                "token_url": "https://gitlab.com/oauth/token",
                "user_url": "https://gitlab.com/api/v4/user",
                "client_id": os.getenv("GITLAB_CLIENT_ID"),
                "client_secret": os.getenv("GITLAB_CLIENT_SECRET"),
                "redirect_uri": os.getenv("GITLAB_REDIRECT_URI"),
                "scope": "api read_user",
            },
            "jira": {
                "name": "Jira",
                "auth_url": "https://auth.atlassian.com/authorize",
                "token_url": "https://auth.atlassian.com/oauth/token",
                "user_url": "https://api.atlassian.com/me",
                "client_id": os.getenv("JIRA_CLIENT_ID"),
                "client_secret": os.getenv("JIRA_CLIENT_SECRET"),
                "redirect_uri": os.getenv("JIRA_REDIRECT_URI"),
                "scope": "read:jira-work write:jira-work offline_access",
                "audience": "api.atlassian.com",
            },
        }

    async def get_authorization_url(
            self,
            provider: str,
            db: asyncpg.Connection,
            user_id: int) -> str:
        """
        Сгенерировать OAuth authorization URL

        Args:
            provider: Имя провайдера (github, gitlab, jira)
            db: Database connection
            user_id: ID пользователя

        Returns:
            Authorization URL для redirect

        Raises:
            ValueError: Если провайдер не поддерживается
        """
        if provider not in self.providers:
            raise ValueError(f"Провайдер '{provider}' не поддерживается")

        config = self.providers[provider]

        # Проверить что client_id и client_secret настроены
        if not config["client_id"] or not config["client_secret"]:
            raise ValueError(
                f"OAuth credentials для {provider} не настроены. "
                f"Установите {provider.upper()}_CLIENT_ID и {provider.upper()}_CLIENT_SECRET")

        # Сгенерировать CSRF state
        state = secrets.token_urlsafe(32)
        await self._store_state(db, state, provider, user_id)

        # Построить authorization URL
        params = {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "scope": config["scope"],
            "state": state,
            "response_type": "code",
        }

        # Jira требует audience параметр
        if provider == "jira":
            params["audience"] = config["audience"]
            params["prompt"] = "consent"

        url = f"{config['auth_url']}?{urlencode(params)}"

        logger.info("Generated OAuth URL for %s, user_id=%s")
        return url

    async def exchange_code_for_token(
            self,
            provider: str,
            code: str,
            state: str,
            db: asyncpg.Connection) -> Dict:
        """
        Обменять authorization code на access token

        Args:
            provider: Имя провайдера
            code: Authorization code
            state: CSRF state
            db: Database connection

        Returns:
            Token data (access_token, refresh_token, expires_in)

        Raises:
            ValueError: Если state невалиден или провайдер не поддерживается
            httpx.HTTPError: Если запрос к провайдеру не удался
        """
        if provider not in self.providers:
            raise ValueError(f"Провайдер '{provider}' не поддерживается")

        # Проверить state (CSRF защита)
        user_id = await self._verify_state(db, state, provider)
        if not user_id:
            raise ValueError("Invalid state parameter")

        config = self.providers[provider]

        # Обменять code на token
        async with httpx.AsyncClient() as client:
            try:
