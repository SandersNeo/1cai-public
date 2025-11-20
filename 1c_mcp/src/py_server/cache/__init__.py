# [NEXUS IDENTITY] ID: 3583055188656704480 | DATE: 2025-11-19

"""
Cache Module - Модуль кэширования для 1C MCP сервера

Предоставляет:
- OAuthTokenCache: кэширование OAuth2 токенов с автоматической очисткой
- SessionManager: управление пользовательскими сессиями
- TokenValidator: валидация и обновление токенов
- SecureStorage: безопасное хранение чувствительных данных
- OAuthCacheManager: единый интерфейс управления кэшем

Все компоненты реализованы с учетом стандартов безопасности:
- Шифрование чувствительных данных
- Автоматическая очистка истекших токенов
- Контроль доступа и мониторинг
- Интеграция с существующим OAuth2 модулем
"""

from .oauth_cache import (
    OAuthCacheManager,
    OAuthTokenCache,
    SessionManager, 
    TokenValidator,
    SecureStorage,
    CachedToken,
    UserSession,
    CacheStrategy,
    SecurityLevel,
    OAuthCacheFactory
)

__version__ = "1.0.0"
__author__ = "1C MCP Development Team"

# Экспорт основных компонентов
__all__ = [
    # Основные классы
    'OAuthCacheManager',
    'OAuthTokenCache',
    'SessionManager',
    'TokenValidator',
    'SecureStorage',
    
    # Структуры данных
    'CachedToken',
    'UserSession',
    
    # Перечисления
    'CacheStrategy',
    'SecurityLevel',
    
    # Фабрика
    'OAuthCacheFactory'
]

# Версия модуля
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable"
}

def get_version() -> str:
    """Получение версии модуля."""
    return f"{VERSION_INFO['major']}.{VERSION_INFO['minor']}.{VERSION_INFO['patch']}"

def create_cache_instance(environment: str = "production", **kwargs) -> OAuthCacheManager:
    """
    Создание экземпляра кэша для указанного окружения.
    
    Args:
        environment: Тип окружения (production, development, test)
        **kwargs: Дополнительные параметры
        
    Returns:
        OAuthCacheManager: Экземпляр менеджера кэша
    """
    if environment == "production":
        return OAuthCacheFactory.create_production_cache(**kwargs)
    elif environment == "development":
        return OAuthCacheFactory.create_development_cache(**kwargs)
    elif environment == "test":
        return OAuthCacheFactory.create_test_cache(**kwargs)
    else:
        raise ValueError(f"Неподдерживаемое окружение: {environment}")

# Инициализация модуля
logger = __import__('logging').getLogger(__name__)
logger.info(f"Cache module v{get_version()} инициализирован")