"""
Internationalization (i18n) Service
Сервис мультиязычности для 1C AI Stack
Поддержка: RU, EN (расширяемо)
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


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
            logger.warning(f"Translations directory not found: {translations_dir}")
            return
        
        # Загружаем все файлы переводов
        for lang in Language:
            lang_file = translations_dir / f"{lang.value}.json"
            
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang.value] = json.load(f)
                    logger.info(f"Loaded translations for {lang.value}")
                except Exception as e:
                    logger.error(f"Failed to load {lang_file}: {e}")
            else:
                logger.warning(f"Translation file not found: {lang_file}")
    
    def t(
        self,
        key: str,
        language: Optional[Language] = None,
        **kwargs
    ) -> str:
        """
        Перевод ключа на указанный язык
        
        Args:
            key: Ключ перевода (например, "bot.welcome")
            language: Язык (None = default)
            **kwargs: Параметры для форматирования
        
        Returns:
            Переведенная строка
        
        Example:
            >>> i18n.t("bot.welcome", name="John")
            "Привет, John!"
        """
        lang = (language or self.default_language).value
        
        # Получаем перевод
        translation = self._get_translation(key, lang)
        
        # Форматируем с параметрами
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing parameter {e} for key {key}")
        
        return translation
    
    def _get_translation(self, key: str, lang: str) -> str:
        """Получить перевод по ключу"""
        
        # Получаем словарь переводов для языка
        lang_dict = self.translations.get(lang, {})
        
        # Поддержка вложенных ключей: "bot.welcome.message"
        keys = key.split('.')
        value = lang_dict
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Ключ не найден - fallback на default язык
                if lang != self.default_language.value:
                    return self._get_translation(key, self.default_language.value)
                
                # Если и в default нет - возвращаем ключ
                logger.warning(f"Translation not found: {key} (lang: {lang})")
                return f"[{key}]"
        
        return str(value)
    
    def get_available_languages(self) -> list[str]:
        """Получить список доступных языков"""
        return list(self.translations.keys())
    
    def set_default_language(self, language: Language):
        """Установить язык по умолчанию"""
        self.default_language = language
        logger.info(f"Default language set to: {language.value}")
    
    def reload_translations(self):
        """Перезагрузить переводы (для hot reload)"""
        self.translations.clear()
        self._load_translations()
        logger.info("Translations reloaded")
    
    def add_custom_translation(self, key: str, language: Language, value: str):
        """
        Добавить кастомный перевод в runtime
        
        Useful для:
        - Кастомизации под клиента
        - A/B тестирования формулировок
        - Временных изменений без редактирования файлов
        """
        lang = language.value
        
        if lang not in self.translations:
            self.translations[lang] = {}
        
        # Поддержка вложенных ключей
        keys = key.split('.')
        current = self.translations[lang]
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        logger.info(f"Added custom translation: {key} ({lang})")


# Singleton instance
_i18n_service: Optional[I18nService] = None


def get_i18n_service(default_language: Language = Language.RU) -> I18nService:
    """Получить глобальный экземпляр сервиса"""
    global _i18n_service
    
    if _i18n_service is None:
        _i18n_service = I18nService(default_language)
    
    return _i18n_service


def t(key: str, language: Optional[Language] = None, **kwargs) -> str:
    """
    Shortcut для перевода
    
    Example:
        >>> from src.services.i18n_service import t
        >>> t("bot.welcome", name="John")
    """
    return get_i18n_service().t(key, language, **kwargs)

