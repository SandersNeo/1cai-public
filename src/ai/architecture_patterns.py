"""
Architecture Pattern Database

Comprehensive collection of architecture patterns for 1C systems:
- FAANG-proven patterns
- BSL-specific adaptations
- Anti-patterns to avoid
- Pattern matching and suggestions
"""

from enum import Enum
from typing import Any, Dict, List, Optional


class PatternCategory(Enum):
    """Pattern categories"""
    ARCHITECTURE = "architecture"
    MICROSERVICES = "microservices"
    DATA = "data"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ANTI_PATTERN = "anti_pattern"


class ArchitecturePattern:
    """Architecture pattern definition"""

    def __init__(
        self,
        name: str,
        category: PatternCategory,
        description: str,
        use_cases: List[str],
        benefits: List[str],
        drawbacks: List[str],
        bsl_adaptation: str,
        examples: List[str],
        related_patterns: List[str] = None
    ):
        self.name = name
        self.category = category
        self.description = description
        self.use_cases = use_cases
        self.benefits = benefits
        self.drawbacks = drawbacks
        self.bsl_adaptation = bsl_adaptation
        self.examples = examples
        self.related_patterns = related_patterns or []


# Architecture Patterns Database
ARCHITECTURE_PATTERNS = {
    # Clean Architecture Family
    "hexagonal": ArchitecturePattern(
        name="Hexagonal Architecture (Ports & Adapters)",
        category=PatternCategory.ARCHITECTURE,
        description="""
        Архитектура, изолирующая бизнес-логику от внешних зависимостей
        через порты (интерфейсы) и адаптеры (реализации).
        """,
        use_cases=[
            "Тестируемость кода",
            "Независимость от фреймворков",
            "Замена внешних сервисов",
            "Модульная конфигурация 1С"
        ],
        benefits=[
            "Высокая тестируемость",
            "Легкая замена зависимостей",
            "Четкое разделение ответственности",
            "Независимость от платформы 1С"
        ],
        drawbacks=[
            "Больше кода (интерфейсы)",
            "Сложность для простых задач",
            "Требует дисциплины команды"
        ],
        bsl_adaptation="""
        В 1С реализуется через:
        - Общие модули как порты (интерфейсы)
        - Модули объектов как адаптеры
        - Разделение на слои: Domain, Application, Infrastructure

        Пример структуры:
        - ОбщиеМодули/ДоменСлой_* (бизнес-логика)
        - ОбщиеМодули/ПриложениеСлой_* (use cases)
        - ОбщиеМодули/ИнфраструктураСлой_* (внешние зависимости)
        """,
        examples=[
            "Netflix microservices architecture",
            "Clean Architecture by Uncle Bob",
            "1C модульная конфигурация"
        ],
        related_patterns=["clean_architecture", "ddd", "onion_architecture"]
    ),

    "clean_architecture": ArchitecturePattern(
        name="Clean Architecture",
        category=PatternCategory.ARCHITECTURE,
        description="""
        Архитектура с концентрическими слоями, где зависимости
        направлены внутрь к бизнес-логике.
        """,
        use_cases=[
            "Долгосрочные проекты",
            "Сложная бизнес-логика",
            "Частые изменения требований",
            "Enterprise 1C системы"
        ],
        benefits=[
            "Независимость от UI и БД",
            "Тестируемость",
            "Гибкость к изменениям",
            "Понятная структура"
        ],
        drawbacks=[
            "Overhead для простых задач",
            "Кривая обучения",
            "Больше файлов/модулей"
        ],
        bsl_adaptation="""
        Слои в 1С:
        1. Entities (Сущности) - справочники, документы
        2. Use Cases (Сценарии) - общие модули с бизнес-логикой
        3. Interface Adapters - модули форм, HTTP сервисы
        4. Frameworks & Drivers - платформа 1С

        Правило зависимостей: внешние слои зависят от внутренних
        """,
        examples=[
            "Uncle Bob's Clean Architecture",
            "1C EDT проекты с Clean Architecture"
        ],
        related_patterns=["hexagonal", "ddd", "cqrs"]
    ),

    # CQRS & Event Sourcing
    "cqrs": ArchitecturePattern(
        name="CQRS (Command Query Responsibility Segregation)",
        category=PatternCategory.DATA,
        description="""
        Разделение операций чтения и записи на разные модели.
        """,
        use_cases=[
            "Разная нагрузка на чтение/запись",
            "Сложные запросы отчетности",
            "Оптимизация производительности",
            "Регистры 1С с разными представлениями"
        ],
        benefits=[
            "Оптимизация чтения и записи отдельно",
            "Масштабируемость",
            "Упрощение сложных запросов",
            "Разные модели данных"
        ],
        drawbacks=[
            "Eventual consistency",
            "Сложность синхронизации",
            "Дублирование кода"
        ],
        bsl_adaptation="""
        В 1С через регистры:
        - Command: Документы (запись)
        - Query: Регистры накопления/сведений (чтение)
        - Разные представления данных для отчетов

        Пример:
        - Документ "Продажа" (команда записи)
        - Регистр "ОстаткиТоваров" (модель чтения)
        - Регистр "АналитикаПродаж" (оптимизированная модель для отчетов)
        """,
        examples=[
            "Martin Fowler CQRS",
            "1C регистры как CQRS",
            "Event-driven 1C системы"
        ],
        related_patterns=["event_sourcing", "ddd", "eventual_consistency"]
    ),

    "event_sourcing": ArchitecturePattern(
        name="Event Sourcing",
        category=PatternCategory.DATA,
        description="""
        Хранение всех изменений состояния как последовательности событий.
        """,
        use_cases=[
            "Audit trail",
            "Временные запросы (на дату)",
            "Восстановление состояния",
            "Документы 1С с проведением"
        ],
        benefits=[
            "Полная история изменений",
            "Возможность replay событий",
            "Audit из коробки",
            "Temporal queries"
        ],
        drawbacks=[
            "Сложность запросов текущего состояния",
            "Объем данных",
            "Сложность миграций"
        ],
        bsl_adaptation="""
        В 1С естественная реализация:
        - Документы = события
        - Движения документов = изменения состояния
        - Регистры = проекции событий
        - Проведение = применение событий

        Дополнительно:
        - Регистр сведений для хранения событий
        - Механизм подписок на события
        """,
        examples=[
            "1C документы и движения",
            "Event Store",
            "CQRS + Event Sourcing"
        ],
        related_patterns=["cqrs", "event_driven", "saga"]
    ),

    # Domain-Driven Design
    "ddd": ArchitecturePattern(
        name="Domain-Driven Design (DDD)",
        category=PatternCategory.ARCHITECTURE,
        description="""
        Проектирование, ориентированное на предметную область (домен).
        """,
        use_cases=[
            "Сложная бизнес-логика",
            "Большие команды",
            "Долгосрочные проекты",
            "Enterprise 1C конфигурации"
        ],
        benefits=[
            "Единый язык с бизнесом",
            "Модульность по доменам",
            "Инкапсуляция бизнес-правил",
            "Масштабируемость команды"
        ],
        drawbacks=[
            "Высокая сложность",
            "Требует экспертизы домена",
            "Overhead для простых задач"
        ],
        bsl_adaptation="""
        DDD концепции в 1С:
        - Bounded Context = подсистема
        - Aggregate = документ + связанные объекты
        - Entity = справочник/документ
        - Value Object = структура
        - Repository = менеджер объекта
        - Domain Service = общий модуль

        Пример:
        Подсистема "Продажи" (Bounded Context):
        - Документ "Заказ" (Aggregate Root)
        - Справочник "Товар" (Entity)
        - Структура "Адрес" (Value Object)
        """,
        examples=[
            "Eric Evans DDD",
            "1C подсистемы как Bounded Contexts",
            "Модульная конфигурация 1С"
        ],
        related_patterns=["hexagonal", "cqrs", "microservices"]
    ),

    # Microservices
    "domain_oriented_microservices": ArchitecturePattern(
        name="Domain-Oriented Microservices",
        category=PatternCategory.MICROSERVICES,
        description="""
        Микросервисы, организованные вокруг доменов, а не технических слоев.
        """,
        use_cases=[
            "Большие распределенные системы",
            "Независимые команды",
            "Разная технологическая база",
            "Интеграция 1С с внешними системами"
        ],
        benefits=[
            "Независимое развертывание",
            "Технологическая независимость",
            "Масштабируемость команд",
            "Отказоустойчивость"
        ],
        drawbacks=[
            "Сложность координации",
            "Distributed transactions",
            "Overhead на коммуникацию",
            "Сложность тестирования"
        ],
        bsl_adaptation="""
        В экосистеме 1С:
        - 1С как микросервис (HTTP/REST API)
        - Разные базы 1С как микросервисы
        - Интеграция через HTTP-сервисы
        - Event-driven через NATS/RabbitMQ

        Паттерны интеграции:
        - API Gateway (nginx)
        - Service Mesh (для множества баз)
        - Event Bus (NATS)
        """,
        examples=[
            "Uber domain-oriented services",
            "1C + микросервисы на Python/Node.js",
            "Распределенная система с несколькими базами 1С"
        ],
        related_patterns=["ddd", "api_gateway", "event_driven"]
    ),

    # Integration Patterns
    "api_gateway": ArchitecturePattern(
        name="API Gateway",
        category=PatternCategory.INTEGRATION,
        description="""
        Единая точка входа для всех клиентских запросов к микросервисам.
        """,
        use_cases=[
            "Множество микросервисов",
            "Разные клиенты (web, mobile)",
            "Централизованная аутентификация",
            "1C + внешние сервисы"
        ],
        benefits=[
            "Упрощение клиентов",
            "Централизованная безопасность",
            "Агрегация запросов",
            "Версионирование API"
        ],
        drawbacks=[
            "Single point of failure",
            "Bottleneck при высокой нагрузке",
            "Дополнительная сложность"
        ],
        bsl_adaptation="""
        Для 1С систем:
        - nginx как API Gateway перед 1С
        - Маршрутизация к разным базам
        - Кэширование ответов
        - Rate limiting
        - JWT аутентификация

        Конфигурация nginx:
        location /api/sales { proxy_pass http://1c_sales; }
        location /api/warehouse { proxy_pass http://1c_warehouse; }
        """,
        examples=[
            "Netflix Zuul",
            "Kong API Gateway",
            "nginx перед 1С HTTP-сервисами"
        ],
        related_patterns=["microservices", "bff", "service_mesh"]
    ),

    # Performance Patterns
    "caching_strategy": ArchitecturePattern(
        name="Multi-Level Caching",
        category=PatternCategory.PERFORMANCE,
        description="""
        Многоуровневое кэширование для оптимизации производительности.
        """,
        use_cases=[
            "Частые повторяющиеся запросы",
            "Дорогие вычисления",
            "Справочная информация",
            "Отчеты 1С"
        ],
        benefits=[
            "Снижение нагрузки на БД",
            "Быстрый отклик",
            "Масштабируемость",
            "Снижение затрат"
        ],
        drawbacks=[
            "Сложность инвалидации",
            "Потребление памяти",
            "Stale data риск"
        ],
        bsl_adaptation="""
        Уровни кэша в 1С:
        1. Клиентский кэш (переменные модуля формы)
        2. Серверный кэш (переменные модуля сеанса)
        3. Redis (внешний кэш)
        4. CDN (для статики)

        Стратегии:
        - Cache-Aside (проверка перед запросом)
        - Write-Through (запись в кэш и БД)
        - Write-Behind (отложенная запись)

        Пример:
        Кэширование справочников в модуле сеанса
        """,
        examples=[
            "Redis multi-level cache",
            "1C кэш в модуле сеанса",
            "CDN для 1C публикаций"
        ],
        related_patterns=["read_through", "write_through", "cache_aside"]
    ),

    # Anti-Patterns
    "nanoservices": ArchitecturePattern(
        name="Nanoservices (Anti-pattern)",
        category=PatternCategory.ANTI_PATTERN,
        description="""
        Чрезмерное разделение на микросервисы, когда каждая функция - отдельный сервис.
        """,
        use_cases=[
            "ИЗБЕГАТЬ: Не использовать этот паттерн!"
        ],
        benefits=[],
        drawbacks=[
            "Огромный overhead на коммуникацию",
            "Сложность отладки",
            "Проблемы с производительностью",
            "Невозможность поддерживать"
        ],
        bsl_adaptation="""
        Признаки nanoservices в 1С:
        - Каждый справочник в отдельной базе
        - HTTP-сервис для каждой функции
        - Чрезмерная модульность

        Как избежать:
        - Группировать по доменам (DDD)
        - Один микросервис = один Bounded Context
        - Минимум 5-10 функций на сервис
        """,
        examples=[
            "Uber nanoservices problem",
            "Переход от nanoservices к domain services"
        ],
        related_patterns=["domain_oriented_microservices", "ddd"]
    ),

    "god_object": ArchitecturePattern(
        name="God Object (Anti-pattern)",
        category=PatternCategory.ANTI_PATTERN,
        description="""
        Объект, который знает/делает слишком много.
        """,
        use_cases=[
            "ИЗБЕГАТЬ: Не использовать этот паттерн!"
        ],
        benefits=[],
        drawbacks=[
            "Нарушение SRP",
            "Сложность тестирования",
            "Tight coupling",
            "Невозможность переиспользования"
        ],
        bsl_adaptation="""
        Признаки God Object в 1С:
        - Общий модуль с 1000+ строк
        - Модуль объекта с десятками методов
        - Один документ для всех операций

        Как исправить:
        - Разделить по ответственности (SRP)
        - Выделить Domain Services
        - Использовать композицию

        Пример рефакторинга:
        ОбщийМодуль "РаботаСДокументами" (God Object)
        →
        - "РаботаСПродажами"
        - "РаботаСЗакупками"
        - "РаботаСОплатами"
        """,
        examples=[
            "Monolithic utility classes",
            "1C общие модули с тысячами строк"
        ],
        related_patterns=["srp", "separation_of_concerns"]
    ),
}


class PatternMatcher:
    """Pattern matching and suggestion engine"""

    def __init__(self):
        self.patterns = ARCHITECTURE_PATTERNS

    def suggest_patterns(
        self,
        problem_description: str,
        context: Dict[str, Any] = None
    ) -> List[ArchitecturePattern]:
        """
        Suggest patterns based on problem description

        Args:
            problem_description: Description of the problem
            context: Additional context (domain, scale, etc)

        Returns:
            List of suggested patterns
        """
        suggestions = []
        problem_lower = problem_description.lower()

        # Simple keyword matching (can be enhanced with ML)
        keywords_map = {
            "тестируемость": ["hexagonal", "clean_architecture"],
            "производительность": ["caching_strategy", "cqrs"],
            "микросервисы": ["domain_oriented_microservices", "api_gateway"],
            "бизнес-логика": ["ddd", "clean_architecture"],
            "события": ["event_sourcing", "cqrs"],
            "интеграция": ["api_gateway", "event_driven"],
            "масштабируемость": ["microservices", "cqrs"],
        }

        for keyword, pattern_keys in keywords_map.items():
            if keyword in problem_lower:
                for key in pattern_keys:
                    if key in self.patterns:
                        pattern = self.patterns[key]
                        if pattern not in suggestions:
                            suggestions.append(pattern)

        return suggestions[:5]  # Top 5

    def get_pattern(self, pattern_key: str) -> Optional[ArchitecturePattern]:
        """Get pattern by key"""
        return self.patterns.get(pattern_key)

    def get_patterns_by_category(
        self,
        category: PatternCategory
    ) -> List[ArchitecturePattern]:
        """Get all patterns in category"""
        return [
            p for p in self.patterns.values()
            if p.category == category
        ]

    def get_anti_patterns(self) -> List[ArchitecturePattern]:
        """Get all anti-patterns"""
        return self.get_patterns_by_category(PatternCategory.ANTI_PATTERN)

    def validate_architecture(
        self,
        architecture_description: str
    ) -> Dict[str, Any]:
        """
        Validate architecture against anti-patterns

        Args:
            architecture_description: Description of architecture

        Returns:
            Validation results with warnings
        """
        warnings = []
        desc_lower = architecture_description.lower()

        # Check for anti-patterns
        anti_pattern_indicators = {
            "god_object": ["один модуль", "все в одном", "универсальный"],
            "nanoservices": ["каждая функция", "отдельный сервис для"],
        }

        for anti_pattern_key, indicators in anti_pattern_indicators.items():
            for indicator in indicators:
                if indicator in desc_lower:
                    pattern = self.get_pattern(anti_pattern_key)
                    if pattern:
                        warnings.append({
                            "type": "anti_pattern",
                            "pattern": pattern.name,
                            "description": pattern.description,
                            "recommendation": f"Избегайте {pattern.name}"
                        })

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "score": max(0, 100 - len(warnings) * 20)
        }


# Singleton instance
_pattern_matcher: Optional[PatternMatcher] = None


def get_pattern_matcher() -> PatternMatcher:
    """Get or create pattern matcher singleton"""
    global _pattern_matcher

    if _pattern_matcher is None:
        _pattern_matcher = PatternMatcher()

    return _pattern_matcher


__all__ = [
    "ArchitecturePattern",
    "PatternCategory",
    "PatternMatcher",
    "ARCHITECTURE_PATTERNS",
    "get_pattern_matcher"
]
