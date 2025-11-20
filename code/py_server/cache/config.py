# [NEXUS IDENTITY] ID: 9059247491361480765 | DATE: 2025-11-19

"""
Конфигурация для MCP Tools Cache

Содержит настройки кэширования для различных окружений и сценариев использования.

Версия: 1.0.0
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class CacheConfig:
    """Конфигурация кэша"""
    
    # Основные параметры
    max_size_mb: int = 100
    default_ttl_stable: float = 30 * 60  # 30 минут
    default_ttl_dynamic: float = 5 * 60   # 5 минут
    persistent_cache_dir: Optional[str] = None
    
    # Стратегия кэширования
    strategy: str = "ttl"  # "lru" или "ttl"
    
    # Настройки производительности
    enable_metrics: bool = True
    enable_monitoring: bool = True
    cleanup_interval_seconds: int = 3600  # 1 час
    
    # Настройки persistent cache
    persistent_enabled: bool = True
    compression_enabled: bool = False
    encryption_enabled: bool = False
    
    # Настройки инвалидации
    auto_cleanup_expired: bool = True
    max_eviction_batch: int = 100
    
    # Мониторинг и алерты
    alert_threshold_hit_ratio: float = 0.7  # alert если hit ratio < 70%
    alert_threshold_memory_usage: float = 0.9  # alert если используется > 90% памяти
    alert_threshold_error_rate: float = 0.05  # alert если ошибок > 5%
    
    def __post_init__(self):
        """Валидация конфигурации"""
        if self.max_size_mb <= 0:
            raise ValueError("max_size_mb должен быть положительным")
        
        if self.default_ttl_stable <= 0:
            raise ValueError("default_ttl_stable должен быть положительным")
        
        if self.default_ttl_dynamic <= 0:
            raise ValueError("default_ttl_dynamic должен быть положительным")
        
        if self.strategy not in ["lru", "ttl"]:
            raise ValueError("strategy должен быть 'lru' или 'ttl'")
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Создаёт конфигурацию из переменных окружения"""
        return cls(
            max_size_mb=int(os.getenv('CACHE_MAX_SIZE_MB', '100')),
            default_ttl_stable=float(os.getenv('CACHE_TTL_STABLE', '1800')),
            default_ttl_dynamic=float(os.getenv('CACHE_TTL_DYNAMIC', '300')),
            persistent_cache_dir=os.getenv('CACHE_PERSISTENT_DIR'),
            strategy=os.getenv('CACHE_STRATEGY', 'ttl'),
            enable_metrics=os.getenv('CACHE_ENABLE_METRICS', 'true').lower() == 'true',
            enable_monitoring=os.getenv('CACHE_ENABLE_MONITORING', 'true').lower() == 'true',
            cleanup_interval_seconds=int(os.getenv('CACHE_CLEANUP_INTERVAL', '3600')),
            persistent_enabled=os.getenv('CACHE_PERSISTENT_ENABLED', 'true').lower() == 'true',
            compression_enabled=os.getenv('CACHE_COMPRESSION_ENABLED', 'false').lower() == 'true',
            encryption_enabled=os.getenv('CACHE_ENCRYPTION_ENABLED', 'false').lower() == 'true',
            auto_cleanup_expired=os.getenv('CACHE_AUTO_CLEANUP', 'true').lower() == 'true',
            max_eviction_batch=int(os.getenv('CACHE_MAX_EVICTION_BATCH', '100')),
            alert_threshold_hit_ratio=float(os.getenv('CACHE_ALERT_HIT_RATIO', '0.7')),
            alert_threshold_memory_usage=float(os.getenv('CACHE_ALERT_MEMORY_USAGE', '0.9')),
            alert_threshold_error_rate=float(os.getenv('CACHE_ALERT_ERROR_RATE', '0.05'))
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'CacheConfig':
        """Создаёт конфигурацию из словаря"""
        return cls(**config_dict)


@dataclass
class DataTypeConfig:
    """Конфигурация типов данных"""
    
    ttl: float
    persistent: bool = False
    max_size_bytes: Optional[int] = None
    compression: bool = False
    encryption: bool = False
    
    def __post_init__(self):
        """Валидация конфигурации типа данных"""
        if self.ttl <= 0:
            raise ValueError("ttl должен быть положительным")


class CacheTypeConfigs:
    """Конфигурации типов данных кэша"""
    
    # Предопределённые конфигурации
    METADATA = DataTypeConfig(
        ttl=30 * 60,  # 30 минут
        persistent=True,
        compression=True
    )
    
    AGGREGATES = DataTypeConfig(
        ttl=5 * 60,   # 5 минут
        persistent=False,
        compression=True
    )
    
    TOOL_CONFIG = DataTypeConfig(
        ttl=30 * 60,  # 30 минут
        persistent=True,
        compression=False
    )
    
    API_RESPONSE = DataTypeConfig(
        ttl=5 * 60,   # 5 минут
        persistent=False,
        compression=True
    )
    
    STABLE = DataTypeConfig(
        ttl=30 * 60,  # 30 минут
        persistent=True,
        compression=False
    )
    
    DYNAMIC = DataTypeConfig(
        ttl=5 * 60,   # 5 минут
        persistent=False,
        compression=True
    )
    
    USER_SESSION = DataTypeConfig(
        ttl=2 * 60,   # 2 минуты
        persistent=False,
        compression=False,
        max_size_bytes=1024 * 1024  # 1MB на пользователя
    )
    
    REPORT_DATA = DataTypeConfig(
        ttl=15 * 60,  # 15 минут
        persistent=False,
        compression=True
    )
    
    @classmethod
    def get_config(cls, data_type: str) -> DataTypeConfig:
        """Возвращает конфигурацию для типа данных"""
        configs = {
            'metadata': cls.METADATA,
            'aggregates': cls.AGGREGATES,
            'tool_config': cls.TOOL_CONFIG,
            'api_response': cls.API_RESPONSE,
            'stable': cls.STABLE,
            'dynamic': cls.DYNAMIC,
            'user_session': cls.USER_SESSION,
            'report_data': cls.REPORT_DATA
        }
        
        if data_type not in configs:
            # Возвращаем базовую конфигурацию для неизвестных типов
            return DataTypeConfig(ttl=10 * 60, persistent=False)
        
        return configs[data_type]
    
    @classmethod
    def get_all_configs(cls) -> Dict[str, DataTypeConfig]:
        """Возвращает все конфигурации"""
        return {
            'metadata': cls.METADATA,
            'aggregates': cls.AGGREGATES,
            'tool_config': cls.TOOL_CONFIG,
            'api_response': cls.API_RESPONSE,
            'stable': cls.STABLE,
            'dynamic': cls.DYNAMIC,
            'user_session': cls.USER_SESSION,
            'report_data': cls.REPORT_DATA
        }


class CacheProfiles:
    """Предопределённые профили конфигурации"""
    
    @staticmethod
    def development() -> CacheConfig:
        """Профиль для разработки"""
        return CacheConfig(
            max_size_mb=50,
            default_ttl_stable=15 * 60,  # 15 минут
            default_ttl_dynamic=2 * 60,   # 2 минуты
            persistent_cache_dir="./cache_dev",
            strategy="lru",
            enable_metrics=True,
            persistent_enabled=False,  # В dev обычно не нужен
            cleanup_interval_seconds=300  # 5 минут
        )
    
    @staticmethod
    def testing() -> CacheConfig:
        """Профиль для тестирования"""
        return CacheConfig(
            max_size_mb=10,
            default_ttl_stable=60,    # 1 минута
            default_ttl_dynamic=30,   # 30 секунд
            persistent_cache_dir=None,
            strategy="ttl",
            enable_metrics=False,
            persistent_enabled=False,
            cleanup_interval_seconds=10  # 10 секунд
        )
    
    @staticmethod
    def staging() -> CacheConfig:
        """Профиль для staging окружения"""
        return CacheConfig(
            max_size_mb=200,
            default_ttl_stable=60 * 60,  # 1 час
            default_ttl_dynamic=10 * 60,  # 10 минут
            persistent_cache_dir="./cache_staging",
            strategy="ttl",
            enable_metrics=True,
            persistent_enabled=True,
            compression_enabled=True,
            cleanup_interval_seconds=1800  # 30 минут
        )
    
    @staticmethod
    def production() -> CacheConfig:
        """Профиль для production"""
        return CacheConfig(
            max_size_mb=1000,  # 1GB
            default_ttl_stable=2 * 60 * 60,  # 2 часа
            default_ttl_dynamic=15 * 60,      # 15 минут
            persistent_cache_dir="/var/cache/mcp_tools",
            strategy="ttl",
            enable_metrics=True,
            persistent_enabled=True,
            compression_enabled=True,
            encryption_enabled=True,
            cleanup_interval_seconds=3600,  # 1 час
            alert_threshold_hit_ratio=0.8,  # 80%
            alert_threshold_memory_usage=0.85,  # 85%
            alert_threshold_error_rate=0.02  # 2%
        )
    
    @staticmethod
    def high_load() -> CacheConfig:
        """Профиль для высоконагруженных систем"""
        return CacheConfig(
            max_size_mb=2000,  # 2GB
            default_ttl_stable=4 * 60 * 60,  # 4 часа
            default_ttl_dynamic=30 * 60,     # 30 минут
            persistent_cache_dir="/fast_ssd/cache",
            strategy="ttl",
            enable_metrics=True,
            persistent_enabled=True,
            compression_enabled=True,
            encryption_enabled=True,
            cleanup_interval_seconds=1800,  # 30 минут
            max_eviction_batch=500,
            alert_threshold_hit_ratio=0.85,  # 85%
            alert_threshold_memory_usage=0.8,  # 80%
            alert_threshold_error_rate=0.01  # 1%
        )
    
    @staticmethod
    def low_memory() -> CacheConfig:
        """Профиль для систем с ограниченной памятью"""
        return CacheConfig(
            max_size_mb=25,
            default_ttl_stable=10 * 60,  # 10 минут
            default_ttl_dynamic=2 * 60,   # 2 минуты
            persistent_cache_dir="./cache_low_mem",
            strategy="lru",
            enable_metrics=True,
            persistent_enabled=True,
            compression_enabled=True,
            cleanup_interval_seconds=600,  # 10 минут
            max_eviction_batch=50
        )


class EnvironmentDetector:
    """Определение окружения для автоматического выбора профиля"""
    
    @staticmethod
    def get_environment() -> str:
        """Определяет текущее окружение"""
        env = os.getenv('ENVIRONMENT', '').lower()
        if env in ['development', 'dev']:
            return 'development'
        elif env in ['testing', 'test']:
            return 'testing'
        elif env in ['staging', 'stage']:
            return 'staging'
        elif env in ['production', 'prod']:
            return 'production'
        else:
            # Автоопределение
            if os.getenv('PYTEST_CURRENT_TEST'):
                return 'testing'
            elif os.path.exists('.git'):
                return 'development'
            else:
                return 'production'
    
    @staticmethod
    def get_recommended_config() -> CacheConfig:
        """Возвращает рекомендуемую конфигурацию для окружения"""
        env = EnvironmentDetector.get_environment()
        
        if env == 'development':
            return CacheProfiles.development()
        elif env == 'testing':
            return CacheProfiles.testing()
        elif env == 'staging':
            return CacheProfiles.staging()
        else:  # production
            return CacheProfiles.production()


# Настройки кэширования по инструментам MCP
MCP_TOOL_CACHE_CONFIGS = {
    'get_catalog_info': {'ttl': 30 * 60, 'data_type': 'metadata'},
    'get_document_structure': {'ttl': 30 * 60, 'data_type': 'metadata'},
    'get_register_info': {'ttl': 30 * 60, 'data_type': 'metadata'},
    'get_catalog_list': {'ttl': 10 * 60, 'data_type': 'api_response'},
    'get_document_list': {'ttl': 10 * 60, 'data_type': 'api_response'},
    'get_register_data': {'ttl': 5 * 60, 'data_type': 'api_response'},
    'sales_report': {'ttl': 15 * 60, 'data_type': 'report_data'},
    'inventory_report': {'ttl': 10 * 60, 'data_type': 'report_data'},
    'create_document': {'ttl': 2 * 60, 'data_type': 'dynamic'},
    'update_record': {'ttl': 2 * 60, 'data_type': 'dynamic'},
    'delete_item': {'ttl': 2 * 60, 'data_type': 'dynamic'},
    'user_session': {'ttl': 2 * 60, 'data_type': 'user_session'}
}


def get_tool_cache_config(tool_name: str) -> Dict[str, Any]:
    """
    Возвращает конфигурацию кэширования для MCP инструмента
    
    Args:
        tool_name: Имя инструмента
        
    Returns:
        Словарь с конфигурацией кэширования
    """
    # Точное совпадение
    if tool_name in MCP_TOOL_CACHE_CONFIGS:
        return MCP_TOOL_CACHE_CONFIGS[tool_name]
    
    # Поиск по частичному совпадению
    for pattern, config in MCP_TOOL_CACHE_CONFIGS.items():
        if pattern in tool_name or tool_name in pattern:
            return config
    
    # По умолчанию
    return {'ttl': 10 * 60, 'data_type': 'stable'}


def create_cache_config(**overrides) -> CacheConfig:
    """
    Создаёт конфигурацию кэша с возможностью переопределения параметров
    
    Args:
        **overrides: Параметры для переопределения
        
    Returns:
        Конфигурация кэша
    """
    # Получаем базовую конфигурацию для окружения
    base_config = EnvironmentDetector.get_recommended_config()
    
    # Применяем переопределения
    config_dict = {
        'max_size_mb': base_config.max_size_mb,
        'default_ttl_stable': base_config.default_ttl_stable,
        'default_ttl_dynamic': base_config.default_ttl_dynamic,
        'persistent_cache_dir': base_config.persistent_cache_dir,
        'strategy': base_config.strategy,
        'enable_metrics': base_config.enable_metrics,
        'enable_monitoring': base_config.enable_monitoring,
        'cleanup_interval_seconds': base_config.cleanup_interval_seconds,
        'persistent_enabled': base_config.persistent_enabled,
        'compression_enabled': base_config.compression_enabled,
        'encryption_enabled': base_config.encryption_enabled,
        'auto_cleanup_expired': base_config.auto_cleanup_expired,
        'max_eviction_batch': base_config.max_eviction_batch,
        'alert_threshold_hit_ratio': base_config.alert_threshold_hit_ratio,
        'alert_threshold_memory_usage': base_config.alert_threshold_memory_usage,
        'alert_threshold_error_rate': base_config.alert_threshold_error_rate
    }
    
    # Применяем переопределения
    config_dict.update(overrides)
    
    return CacheConfig(**config_dict)


def validate_config(config: CacheConfig) -> bool:
    """
    Валидирует конфигурацию кэша
    
    Args:
        config: Конфигурация для проверки
        
    Returns:
        True если конфигурация корректна
    """
    try:
        # Проверяем основные параметры
        if config.max_size_mb <= 0:
            return False
        
        if config.default_ttl_stable <= 0 or config.default_ttl_dynamic <= 0:
            return False
        
        if config.strategy not in ['lru', 'ttl']:
            return False
        
        # Проверяем директорию persistent cache
        if config.persistent_enabled and config.persistent_cache_dir:
            cache_dir = Path(config.persistent_cache_dir)
            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError):
                return False
        
        # Проверяем пороговые значения
        if not (0 <= config.alert_threshold_hit_ratio <= 1):
            return False
        
        if not (0 <= config.alert_threshold_memory_usage <= 1):
            return False
        
        if not (0 <= config.alert_threshold_error_rate <= 1):
            return False
        
        return True
        
    except Exception:
        return False


def print_config(config: CacheConfig) -> None:
    """
    Выводит конфигурацию в читаемом виде
    
    Args:
        config: Конфигурация для вывода
    """
    print("=== Конфигурация MCP Tools Cache ===")
    print(f"Максимальный размер: {config.max_size_mb} MB")
    print(f"TTL стабильных данных: {config.default_ttl_stable / 60:.1f} минут")
    print(f"TTL динамических данных: {config.default_ttl_dynamic / 60:.1f} минут")
    print(f"Стратегия: {config.strategy}")
    print(f"Persistent cache: {'включен' if config.persistent_enabled else 'отключен'}")
    if config.persistent_cache_dir:
        print(f"Директория persistent cache: {config.persistent_cache_dir}")
    print(f"Сжатие: {'включено' if config.compression_enabled else 'отключено'}")
    print(f"Шифрование: {'включено' if config.encryption_enabled else 'отключено'}")
    print(f"Интервал очистки: {config.cleanup_interval_seconds / 60:.1f} минут")
    print(f"Мониторинг: {'включен' if config.enable_monitoring else 'отключен'}")
    print(f"Порог alert hit ratio: {config.alert_threshold_hit_ratio:.1%}")
    print(f"Порог alert использования памяти: {config.alert_threshold_memory_usage:.1%}")
    print(f"Порог alert error rate: {config.alert_threshold_error_rate:.1%}")


if __name__ == "__main__":
    # Пример использования
    print("=== Детектор окружения ===")
    env = EnvironmentDetector.get_environment()
    print(f"Определённое окружение: {env}")
    
    print("\n=== Рекомендуемая конфигурация ===")
    recommended_config = EnvironmentDetector.get_recommended_config()
    print_config(recommended_config)
    
    print("\n=== Конфигурация из переменных окружения ===")
    env_config = CacheConfig.from_env()
    print_config(env_config)
    
    print("\n=== Кастомная конфигурация ===")
    custom_config = create_cache_config(
        max_size_mb=200,
        default_ttl_stable=45 * 60,
        strategy="lru"
    )
    print_config(custom_config)
    
    print("\n=== Конфигурации типов данных ===")
    for data_type, config in CacheTypeConfigs.get_all_configs().items():
        print(f"{data_type}: TTL={config.ttl / 60:.1f}мин, "
              f"persistent={config.persistent}, "
              f"compression={config.compression}")
    
    print("\n=== Конфигурации MCP инструментов ===")
    tools_to_check = [
        'get_catalog_info',
        'get_catalog_list', 
        'sales_report',
        'create_document',
        'unknown_tool'
    ]
    
    for tool_name in tools_to_check:
        config = get_tool_cache_config(tool_name)
        print(f"{tool_name}: {config}")
