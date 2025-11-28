# [NEXUS IDENTITY] ID: 6122309749347960075 | DATE: 2025-11-19

"""
Telegram Bot Handlers
Обработчики команд и сообщений
"""

import os
import tempfile
from pathlib import Path

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from src.ai.orchestrator import AIOrchestrator
from src.services.ocr_service import DocumentType, get_ocr_service
from src.services.speech_to_text_service import get_stt_service
from src.telegram.config import config
from src.telegram.formatters import TelegramFormatter
from src.telegram.rate_limiter import RateLimiter
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger
router = Router()

# Services
orchestrator = AIOrchestrator()
formatter = TelegramFormatter()
rate_limiter = RateLimiter(
    max_per_minute=config.max_requests_per_minute,
    max_per_day=config.max_requests_per_day,
)


def is_premium_user(user_id: int) -> bool:
    """Проверка Premium статуса"""
    return user_id in (config.premium_user_ids or set())


async def check_rate_limit(message: Message) -> bool:
    """Проверка rate limit с автоответом"""
    user_id = message.from_user.id
    is_premium = is_premium_user(user_id)

    allowed, error_msg = await rate_limiter.check_limit(user_id, is_premium)

    if not allowed:
        await message.reply(error_msg, parse_mode=ParseMode.MARKDOWN)

    return allowed


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    user_name = message.from_user.first_name

    welcome = f"""👋 Привет, **{user_name}**!

Я — AI-помощник для 1С разработчиков.

Могу:
🔍 Искать код по смыслу (не только по тексту!)
💻 Генерировать BSL код
🔗 Анализировать зависимости
💡 Отвечать на вопросы о вашей конфигурации
🎤 Понимать голосовые сообщения!

**Попробуйте:**
• `/search расчет НДС`
• Или просто спросите: "Где мы работаем с документами?"
• 🎤 Или отправьте голосовое сообщение!

Полный список команд: /help

🚀 **Начнем?**
"""

    await message.reply(welcome, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = formatter.format_help()
    await message.reply(help_text, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("search"))
async def cmd_search(message: Message):
    """Команда /search - семантический поиск"""

    # Rate limiting
    if not await check_rate_limit(message):
        return

    # Извлечение запроса
    query = message.text.replace("/search", "").strip()

    if not query:
        await message.reply(
            "❓ Укажите запрос для поиска\n\n" "Пример: `/search расчет НДС`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Typing indicator
    await message.answer("🔍 Ищу...")

    try:
