# [NEXUS IDENTITY] ID: -330289191117326244 | DATE: 2025-11-19

"""
Telegram Bot Configuration
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""

    # Bot token from @BotFather
    bot_token: str

    # Admin user IDs (для контроля доступа)
    admin_ids: list[int]

    # Rate limiting
    max_requests_per_minute: int = 10
    max_requests_per_day: int = 100

    # Premium users (unlimited)
    premium_user_ids: set[int] = None

    # Features
    enable_code_generation: bool = True
    enable_dependency_analysis: bool = True
    enable_semantic_search: bool = True

    # Webhook settings (для production)
    webhook_url: Optional[str] = None
    webhook_path: str = "/telegram/webhook"
    webhook_port: int = 8443

    @classmethod
    def from_env(cls):
        """Load config from environment variables"""
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            admin_ids=[
                int(id) for id in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if id
            ],
            max_requests_per_minute=int(os.getenv("TELEGRAM_RATE_LIMIT_MIN", "10")),
            max_requests_per_day=int(os.getenv("TELEGRAM_RATE_LIMIT_DAY", "100")),
            premium_user_ids=set(
                [
                    int(id)
                    for id in os.getenv("TELEGRAM_PREMIUM_IDS", "").split(",")
                    if id
                ]
            ),
            enable_code_generation=os.getenv("TELEGRAM_ENABLE_CODEGEN", "true").lower()
            == "true",
            enable_dependency_analysis=os.getenv("TELEGRAM_ENABLE_DEPS", "true").lower()
            == "true",
            enable_semantic_search=os.getenv("TELEGRAM_ENABLE_SEARCH", "true").lower()
            == "true",
            webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL"),
            webhook_path=os.getenv("TELEGRAM_WEBHOOK_PATH", "/telegram/webhook"),
            webhook_port=int(os.getenv("TELEGRAM_WEBHOOK_PORT", "8443")),
        )


# Global config instance
config = TelegramConfig.from_env()
