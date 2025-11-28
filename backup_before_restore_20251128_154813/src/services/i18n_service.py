# [NEXUS IDENTITY] ID: 4085819542034338285 | DATE: 2025-11-19

"""
Internationalization (i18n) Service
Версия: 2.1.0

Улучшения:
- Input validation
- Structured logging
- Улучшена обработка ошибок
"""

import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class Language(str, Enum):
    """Поддерживаемые языки"""

    RU = "ru"
    EN = "en"
    # Для расширения:
    # KZ = "kz"  # Казахский
    # UK = "uk"  # Украинский
    # BY = "by"  # Белорусский


class I18nService:
    """Сервис интернационализации"""

    def __init__(self, default_language: Language = Language.RU):
        """
        Инициализация сервиса

        Args:
            default_language: Язык по умолчанию
        """
        self.default_language = default_language
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """Загрузка переводов из файлов"""
        translations_dir = Path(__file__).parent.parent.parent / "locales"

        if not translations_dir.exists():
            logger.warning(
                "Translations directory not found",
                extra={"translations_dir": str(translations_dir)},
            )
            return

        # Загружаем все файлы переводов
        for lang in Language:
            lang_file = translations_dir / f"{lang.value}.json"

            if lang_file.exists():
                try:
