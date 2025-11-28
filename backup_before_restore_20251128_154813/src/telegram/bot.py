# [NEXUS IDENTITY] ID: 8720553252560500656 | DATE: 2025-11-19

"""
Telegram Bot - Main entry point
Интеграция с 1C AI Assistant
"""

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.telegram.config import config
from src.telegram.handlers import router
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


async def main():
    """Main bot function"""

    # Проверка конфигурации
    if not config.bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        logger.info("Get token from @BotFather: https://t.me/BotFather")
        return

    logger.info("🤖 Starting 1C AI Assistant Telegram Bot...")

    # Initialize bot
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)

    # Startup message
    try:
            "Fatal error",
            extra = {"error": str(e), "error_type": type(e).__name__},
            exc_info = True,
        )
        sys.exit(1)
