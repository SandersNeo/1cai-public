"""
Тестовый скрипт для проверки VLM Server
"""

import asyncio
from pathlib import Path

import httpx


async def test_health():
    """Проверка health endpoint"""
    print("1️⃣ Тест Health Check...")

    async with httpx.AsyncClient() as client:
        try:
