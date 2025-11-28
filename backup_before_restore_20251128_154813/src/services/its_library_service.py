# [NEXUS IDENTITY] ID: -5673062708007166819 | DATE: 2025-11-19

"""
Сервис для работы с библиотекой 1С ИТС
Извлечение документации, примеров кода и best practices
Версия: 2.1.0

Улучшения:
- Retry logic для HTTP запросов
- Улучшена обработка ошибок
- Structured logging
- Input validation
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ITSLibraryService:
    """Сервис для работы с библиотекой 1С ИТС"""

    # URL библиотеки ИТС
    ITS_BASE_URL = "https://its.1c.ru"
    # URL авторизации (правильный URL из login.1c.ru)
    ITS_LOGIN_URL = "https://login.1c.ru/login?service=https%3A%2F%2Fits.1c.ru%2Flogin%2F%3Faction%3Daftercheck%26provider%3Dlogin"

    # Возможные URL для входа (резервные)
    ITS_LOGIN_URLS = [
        "https://login.1c.ru/login?service=https%3A%2F%2Fits.1c.ru%2Flogin%2F%3Faction%3Daftercheck%26provider%3Dlogin",
        "https://its.1c.ru/db/metod8dev",
        "https://its.1c.ru/auth",
        "https://its.1c.ru/login",
    ]

    def __init__(self, username: str, password: str):
        """
        Инициализация сервиса ИТС

        Args:
            username: Имя пользователя ИТС
            password: Пароль ИТС
        """
        # Input validation
        if not username or not isinstance(username, str):
            raise ValueError("Username must be a non-empty string")
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")

        self.username = username
        self.password = password
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        # Для синхронных запросов используем Client
        self.session = httpx.Client(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            headers=self.base_headers,
        )
        self.authenticated = False

    async def authenticate(self) -> bool:
        """
        Авторизация в библиотеке ИТС

        Returns:
            True если авторизация успешна
        """
        try:
