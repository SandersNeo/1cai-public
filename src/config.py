# [NEXUS IDENTITY] ID: 2515925432159965546 | DATE: 2025-11-19

"""
Конфигурация для AI-ассистентов
Версия: 2.0.0

Улучшения:
- Улучшенная валидация настроек
- Environment variable validation
- Type hints для всех полей
- Default values с описаниями
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Настройки приложения с валидацией

    Best practices:
    - Валидация через Pydantic
    - Environment variable support
    - Type safety
    - Default values
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Игнорируем неизвестные поля
    )

    # OpenAI API
    openai_api_key: str = Field(
        default="", description="API ключ OpenAI", validation_alias="OPENAI_API_KEY")

    # Kimi-K2-Thinking (Moonshot AI) - API или локальный режим
    kimi_mode: str = Field(
        default="api",
        description="Режим работы Kimi: 'api' (Moonshot API) или 'local' (Ollama)",
        validation_alias="KIMI_MODE",
    )
    kimi_api_key: str = Field(
        default="",
        description="API ключ Kimi-K2-Thinking (Moonshot AI) - только для API режима",
        validation_alias="KIMI_API_KEY",
    )
    kimi_api_url: str = Field(
        default="https://api.moonshot.cn/v1",
        description="URL API Kimi - только для API режима",
        validation_alias="KIMI_API_URL",
    )
    kimi_model: str = Field(
        default="moonshotai/Kimi-K2-Thinking",
        description="Модель Kimi для API режима",
        validation_alias="KIMI_MODEL",
    )
    kimi_local_model: str = Field(
        default="kimi-k2-thinking:cloud",
        description="Модель Kimi для локального режима (Ollama)",
        validation_alias="KIMI_LOCAL_MODEL",
    )
    kimi_ollama_url: str = Field(
        default="",
        description="URL Ollama для локального режима (по умолчанию использует OLLAMA_HOST)",
        validation_alias="KIMI_OLLAMA_URL",
    )
    kimi_temperature: float = Field(
        default=1.0,
        description="Temperature для Kimi (рекомендуется 1.0)",
        validation_alias="KIMI_TEMPERATURE",
    )

    # Supabase
    supabase_url: str = Field(
        default="", description="URL Supabase проекта", validation_alias="SUPABASE_URL")
    supabase_key: str = Field(
        default="", description="API ключ Supabase", validation_alias="SUPABASE_KEY")

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Валидация OpenAI API ключа"""
        if v and not v.startswith("sk-"):
            logger.warning("OpenAI API key doesn't start with 'sk-', may be invalid")
        return v

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Валидация Supabase URL"""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            logger.warning(
                "Supabase URL doesn't start with http:// or https://",
                extra={"supabase_url": v},
            )
        return v

    # Конфигурация ассистентов
    assistant_configs: Dict[str, Dict[str, Any]] = {
        "architect": {
            "role": "architect",
            "name": "Архитектор AI",
            "description": "Специализированный ассистент для архитектурного анализа и проектирования",
            "temperature": 0.3,
            "max_tokens": 2000,
            "system_prompt": """Ты - опытный архитектор систем 1С с более чем 15-летним опытом работы.

Твоя специализация:
- Анализ бизнес-требований и их преобразование в архитектурные решения
- Проектирование масштабируемых и поддерживаемых систем 1С
- Оценка рисков и предложение мер по их минимизации
- Генерация архитектурных диаграмм в формате Mermaid

Всегда предоставляй:
1. Четкое объяснение принятых решений
2. Обоснование выбора архитектурных паттернов
3. Практические рекомендации по реализации
4. Визуализацию через диаграммы Mermaid

Используй профессиональную терминологию 1С и учитывай специфику российского рынка.""",
            "vector_store_config": {
                "table_name": "architect_knowledge",
                "similarity_threshold": 0.8,
            },
        },
        "developer": {
            "role": "developer",
            "name": "Разработчик AI",
            "description": "Ассистент для помощи в разработке кода 1С",
            "temperature": 0.2,
            "max_tokens": 1500,
            "system_prompt": """Ты - опытный разработчик 1С с глубокими знаниями BSL, запросов и платформы.

Твоя специализация:
- Генерация кода на языке 1С (BSL)
- Оптимизация запросов 1С:Предприятие
- Code review и выявление антипаттернов
- Написание тестов и документации

Всегда предоставляй:
1. Готовый к использованию код
2. Объяснение логики работы
3. Рекомендации по оптимизации
4. Примеры тестирования""",
            "vector_store_config": {
                "table_name": "developer_knowledge",
                "similarity_threshold": 0.7,
            },
        },
        "tester": {
            "role": "tester",
            "name": "Тестировщик AI",
            "description": "Ассистент для создания тестов и обеспечения качества",
            "temperature": 0.3,
            "max_tokens": 1500,
            "system_prompt": """Ты - эксперт по тестированию систем 1С с опытом автоматизации QA.

Твоя специализация:
- Создание тестовых сценариев
- Анализ покрытия тестами
- Выявление критических путей тестирования
- Генерация тестовых данных

Всегда предоставляй:
1. Структурированные тестовые сценарии
2. Классы эквивалентности и граничные значения
3. Рекомендации по автоматизации
4. Метрики качества тестирования""",
            "vector_store_config": {
                "table_name": "tester_knowledge",
                "similarity_threshold": 0.75,
            },
        },
        "pm": {
            "role": "project_manager",
            "name": "Менеджер проектов AI",
            "description": "Ассистент для управления проектами и планирования",
            "temperature": 0.4,
            "max_tokens": 1200,
            "system_prompt": """Ты - опытный менеджер проектов 1С с PMP сертификацией.

Твоя специализация:
- Планирование этапов внедрения 1С
- Оценка временных и ресурсных затрат
- Управление рисками проекта
- Координация команды разработчиков

Всегда предоставляй:
1. Детальные планы работ
2. Оценку рисков и сроков
3. Рекомендации по ресурсам
4. KPI для мониторинга прогресса""",
            "vector_store_config": {
                "table_name": "pm_knowledge",
                "similarity_threshold": 0.7,
            },
        },
        "analyst": {
            "role": "business_analyst",
            "name": "Бизнес-аналитик AI",
            "description": "Ассистент для анализа бизнес-требований и процессов",
            "temperature": 0.3,
            "max_tokens": 1500,
            "system_prompt": """Ты - опытный бизнес-аналитик с опытом внедрения 1С.

Твоя специализация:
- Извлечение требований из бизнес-документов
- Моделирование бизнес-процессов
- Анализ функциональных требований
- Создание пользовательских историй

Всегда предоставляй:
1. Структурированные требования
2. Диаграммы процессов
3. User stories с критериями приемки
4. Анализ пробелов в функциональности""",
            "vector_store_config": {
                "table_name": "analyst_knowledge",
                "similarity_threshold": 0.8,
            },
        },
    }

    # База данных
    database_url: str = Field(
        default="",
        description="URL базы данных (postgresql://user:pass@host:port/db)",
        validation_alias="DATABASE_URL",
    )

    # Redis для кэширования
    redis_url: str = Field(default="redis://localhost:6379", description="URL Redis")

    # CORS настройки
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Разрешенные домены для CORS (через запятую)",
    )

    # JWT настройки
    jwt_secret_key: Optional[str] = Field(
        default=None, description="Секретный ключ для JWT")
    jwt_algorithm: str = Field(default="HS256", description="Алгоритм подписи JWT")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Время жизни access token в минутах")

    # Путь к логам
    log_dir: str = Field(default="./logs", description="Директория для логов", validation_alias="LOG_DIR")
    log_file: str = Field(default="app.log", description="Имя файла лога", validation_alias="LOG_FILE")
    log_level: str = Field(default="INFO", description="Уровень логирования", validation_alias="LOG_LEVEL")

    # Режим разработки (для development можно разрешить небезопасные настройки)
    environment: str = Field(default="production",
                             description="Режим работы: development/production")

    # Внешние MCP-инструменты
    mcp_bsl_context_base_url: Optional[str] = Field(
        default=None,
        description="Базовый URL MCP сервера платформенного контекста (например, alkoleft/mcp-bsl-platform-context)",
    )
    mcp_bsl_context_tool_name: str = Field(
        default="platform_context",
        description="Название инструмента на внешнем MCP сервере для получения платформенного контекста",
    )
    mcp_bsl_context_auth_token: Optional[str] = Field(
        default=None,
        description="Bearer-токен для аутентификации на MCP сервере платформенного контекста (опционально)",
    )
    mcp_bsl_test_runner_base_url: Optional[str] = Field(
        default=None,
        description="Базовый URL MCP сервера тест-раннера (например, alkoleft/mcp-onec-test-runner)",
    )
    mcp_bsl_test_runner_tool_name: str = Field(
        default="run_tests",
        description="Название инструмента на MCP сервере тест-раннера",
    )
    mcp_bsl_test_runner_auth_token: Optional[str] = Field(
        default=None,
        description="Bearer-токен для аутентификации на MCP сервере тест-раннера (опционально)",
    )

    # Nested Learning feature flags
    use_nested_learning: bool = Field(
        default=False,
        description="Enable Nested Learning for continual learning (experimental)",
        validation_alias="USE_NESTED_LEARNING",
    )
    use_adaptive_selection: bool = Field(
        default=False, description="Enable adaptive LLM provider selection", validation_alias="USE_ADAPTIVE_SELECTION"
    )
    use_nested_completion: bool = Field(
        default=False, description="Enable multi-level code completion", validation_alias="USE_NESTED_COMPLETION"
    )

    # --- Infrastructure ---
    otlp_endpoint: Optional[str] = Field(default=None, description="OpenTelemetry Endpoint", validation_alias="OTLP_ENDPOINT")
    enable_legacy_api_redirect: bool = Field(default=True, description="Enable redirect from /api/ to /api/v1/", validation_alias="ENABLE_LEGACY_API_REDIRECT")

    # --- Databases (Fallback/Direct) ---
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="knowledge_base", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="admin", validation_alias="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, validation_alias="POSTGRES_PASSWORD")

    neo4j_uri: str = Field(default="bolt://localhost:7687", validation_alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", validation_alias="NEO4J_USER")
    neo4j_password: str = Field(default="password", validation_alias="NEO4J_PASSWORD")

    qdrant_host: str = Field(default="localhost", validation_alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, validation_alias="QDRANT_PORT")

    es_url: str = Field(default="http://localhost:9200", validation_alias="ES_URL")

    # --- S3 / Minio ---
    aws_s3_bucket: Optional[str] = Field(default=None, validation_alias="AWS_S3_BUCKET")
    minio_default_bucket: Optional[str] = Field(default=None, validation_alias="MINIO_DEFAULT_BUCKET") # Fallback
    aws_s3_region: Optional[str] = Field(default=None, validation_alias="AWS_S3_REGION")
    aws_s3_endpoint: Optional[str] = Field(default=None, validation_alias="AWS_S3_ENDPOINT")
    minio_endpoint: Optional[str] = Field(default=None, validation_alias="MINIO_ENDPOINT") # Fallback
    aws_access_key_id: Optional[str] = Field(default=None, validation_alias="AWS_ACCESS_KEY_ID")
    minio_root_user: Optional[str] = Field(default=None, validation_alias="MINIO_ROOT_USER") # Fallback
    aws_secret_access_key: Optional[str] = Field(default=None, validation_alias="AWS_SECRET_ACCESS_KEY")
    minio_root_password: Optional[str] = Field(default=None, validation_alias="MINIO_ROOT_PASSWORD") # Fallback
    aws_s3_create_bucket: bool = Field(default=True, validation_alias="AWS_S3_CREATE_BUCKET")

    # --- Marketplace & Rate Limits ---
    marketplace_cache_refresh_minutes: int = Field(default=15, validation_alias="MARKETPLACE_CACHE_REFRESH_MINUTES")
    user_rate_limit_per_minute: int = Field(default=60, validation_alias="USER_RATE_LIMIT_PER_MINUTE")
    user_rate_limit_window_seconds: int = Field(default=60, validation_alias="USER_RATE_LIMIT_WINDOW_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    def get_cors_origins(self) -> List[str]:
        """Получить список разрешенных доменов для CORS"""
        if self.environment == "development" and not self.cors_origins:
            return ["*"]  # Только для development
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def get_log_path(self) -> str:
        """Получить полный путь к файлу лога"""
        from pathlib import Path

        log_dir = Path(self.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir / self.log_file)


# Создаем глобальный экземпляр настроек
settings = Settings()

# Export feature flags for easy access
USE_NESTED_LEARNING = settings.use_nested_learning
USE_ADAPTIVE_SELECTION = settings.use_adaptive_selection
USE_NESTED_COMPLETION = settings.use_nested_completion
USE_TEMPORAL_GNN = getattr(settings, "use_temporal_gnn", False)
USE_NESTED_MEMORY = getattr(settings, "use_nested_memory", False)
USE_NESTED_SCENARIOS = getattr(settings, "use_nested_scenarios", False)
USE_DEEP_OPTIMIZER = getattr(settings, "use_deep_optimizer", False)

# Import AdvancedConfigManager for backward compatibility
try:
    from src.config.advanced_config import AdvancedConfigManager
except ImportError:
    # If config/ directory is removed, AdvancedConfigManager won't be available
    # This is fine - it's not used anywhere in the codebase
    AdvancedConfigManager = None
