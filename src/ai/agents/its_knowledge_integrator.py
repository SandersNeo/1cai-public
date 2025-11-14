"""
ITS Knowledge Integrator
Интеграция официальных знаний 1С ИТС в AI Архитектор
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ITSKnowledgeIntegrator:
    """
    Интеграция знаний из базы ИТС
    Предоставляет официальные рекомендации 1С для AI Архитектора
    """
    
    def __init__(self):
        # Подключение к ИТС
        try:
            from src.services.its_library_service import get_its_service
            self.its = get_its_service()
            self.its_available = True
        except Exception as e:
            logger.warning(
                "ITS service not available",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            self.its = None
            self.its_available = False
        
        # Кеш загруженных знаний
        self.knowledge_cache = {}
        
        # Загрузка встроенных знаний из ИТС
        self.architecture_patterns = self._load_architecture_patterns()
        self.performance_tips = self._load_performance_tips()
        self.integration_patterns = self._load_integration_patterns()
        self.code_standards = self._load_code_standards()
    
    # ==========================================
    # АРХИТЕКТУРНЫЕ ПАТТЕРНЫ
    # ==========================================
    
    def _load_architecture_patterns(self) -> Dict[str, Any]:
        """Загрузка архитектурных паттернов из ИТС"""
        return {
            "three_tier_client_server": {
                "name": "Трехуровневая архитектура клиент-сервер",
                "its_url": "https://its.1c.ru/db/metod8dev/src/platform81/review8.1/",
                "description": """
                Между клиентом и СУБД располагается сервер 1С:Предприятия.
                Клиент взаимодействует с сервером, сервер с СУБД.
                """,
                "diagram_mermaid": """
graph LR
    TC[Thin Client] <--> Server[1С:Enterprise Server]
    Server <--> DB[(СУБД)]
    Server --> Cache[Cache]
    LB[Load Balancer] --> Server
                """,
                "best_for": [
                    "Более 100 пользователей",
                    "Распределенная работа",
                    "Высокая доступность",
                    "Веб-доступ"
                ],
                "components": {
                    "client": {
                        "type": "Thin Client",
                        "responsibilities": ["UI", "Ввод данных", "Отображение"],
                        "deployment": "Browser / Thin client app"
                    },
                    "app_server": {
                        "type": "1С:Enterprise Server (кластер)",
                        "responsibilities": [
                            "Бизнес-логика",
                            "Кеширование",
                            "Балансировка нагрузки",
                            "Сессии пользователей"
                        ],
                        "deployment": "Dedicated server(s)",
                        "scaling": "Horizontal (добавление рабочих процессов)"
                    },
                    "database": {
                        "type": "PostgreSQL / MS SQL",
                        "responsibilities": ["Хранение данных", "ACID транзакции"],
                        "deployment": "Database server"
                    }
                },
                "optimization_tips": [
                    "Использовать тонкий клиент для веб-доступа",
                    "Настроить кластер с несколькими рабочими процессами",
                    "Включить кеширование на уровне сервера",
                    "Настроить connection pooling к СУБД",
                    "Балансировка по производительности серверов"
                ],
                "when_to_use": {
                    "users": "> 100",
                    "load": "medium-high",
                    "availability_sla": "> 99%",
                    "budget": "medium-high"
                }
            },
            
            "bi_analytics_architecture": {
                "name": "Аналитическая архитектура (BI)",
                "its_url": "https://its.1c.ru/db/metod8dev/src/developers/additional/analytics/",
                "description": """
                Архитектура для построения Business Intelligence решений.
                Включает ETL, хранилище данных и аналитический слой.
                """,
                "diagram_mermaid": """
graph TD
    OLTP1[1С:ERP] --> ETL[ETL Process]
    OLTP2[1С:ЗУП] --> ETL
    CRM[CRM] --> ETL
    ETL --> DWH[(Data Warehouse)]
    DWH --> OLAP[OLAP Cubes]
    DWH --> BI[1С:Аналитика]
    OLAP --> BI
    BI --> Dashboards[Дашборды]
                """,
                "best_for": [
                    "Отчетность топ-менеджмента",
                    "Консолидированная аналитика",
                    "Multi-source reporting",
                    "Historical trend analysis"
                ],
                "components": {
                    "oltp_sources": "1С конфигурации (транзакционные БД)",
                    "etl": "1С:Универсальный обмен или custom Python/Airflow",
                    "dwh": "PostgreSQL / ClickHouse / Greenplum",
                    "olap": "OLAP cubes (star schema)",
                    "bi_layer": "1С:Аналитика / PowerBI / Tableau"
                },
                "best_practices": [
                    "Разделение OLTP и OLAP (не нагружать транзакционную БД)",
                    "Ночные ETL процессы",
                    "Инкрементальная загрузка (только изменения)",
                    "Star schema для DWH",
                    "Pre-aggregation для ускорения отчетов"
                ]
            },
            
            "rib_distributed": {
                "name": "РИБ (Распределенная информационная база)",
                "its_url": "https://its.1c.ru/db/metod8dev/src/rib/",
                "description": """
                Синхронизация данных между несколькими базами 1С.
                Подходит для холдингов, филиалов, offline работы.
                """,
                "best_for": [
                    "Холдинг с филиалами",
                    "Розничные сети",
                    "Offline операции",
                    "Региональные подразделения"
                ],
                "patterns": {
                    "master_slave": "Головная → филиалы (односторонняя синхронизация)",
                    "peer_to_peer": "Равноправные узлы (двусторонняя)",
                    "hub_and_spoke": "Центральный узел + периферия"
                },
                "use_cases": [
                    "Розничная сеть: каждый магазин = отдельная база",
                    "Холдинг: головная + дочерние компании",
                    "Мобильные точки продаж (offline)"
                ]
            },
            
            "microservices_1c": {
                "name": "Микросервисная архитектура с 1С",
                "its_url": "https://its.1c.ru/db/metod8dev/src/integration/",
                "description": """
                Разделение монолитной конфигурации на независимые сервисы.
                Интеграция через API / Message Bus.
                """,
                "best_for": [
                    "Сложные enterprise системы",
                    "Независимое масштабирование модулей",
                    "Различные команды разработки"
                ],
                "patterns": {
                    "api_gateway": "Kong / Nginx перед 1С HTTP сервисами",
                    "message_bus": "Apache Kafka / RabbitMQ для асинхронности",
                    "service_discovery": "Consul / Eureka для поиска сервисов"
                }
            }
        }
    
    # ==========================================
    # PERFORMANCE TIPS
    # ==========================================
    
    def _load_performance_tips(self) -> Dict[str, Any]:
        """Загрузка tips по производительности из ИТС"""
        return {
            "slow_queries": {
                "title": "Оптимизация медленных запросов",
                "its_source": "https://its.1c.ru/db/metod8dev/",
                "tips": [
                    {
                        "issue": "Полная выборка из большой таблицы",
                        "bad_example": """
// ПЛОХО: Полная выборка
Запрос = Новый Запрос;
Запрос.Текст = "ВЫБРАТЬ * ИЗ РегистрНакопления.Продажи";
Результат = Запрос.Выполнить().Выгрузить();
                        """,
                        "good_example": """
// ХОРОШО: С условиями и индексами
Запрос = Новый Запрос;
Запрос.Текст = "
|ВЫБРАТЬ
|   Номенклатура,
|   СУММА(Сумма) КАК СуммаПродаж
|ИЗ
|   РегистрНакопления.Продажи
|ГДЕ
|   Период МЕЖДУ &ДатаНач И &ДатаКон
|   И Организация = &Организация
|СГРУППИРОВАТЬ ПО
|   Номенклатура
|ИНДЕКСИРОВАТЬ ПО
|   Номенклатура";
                        """,
                        "improvement": "100x ускорение",
                        "explanation": "Индексы, условия WHERE, агрегация на уровне СУБД"
                    },
                    {
                        "issue": "Вложенные циклы с запросами",
                        "bad_example": """
// ПЛОХО: N+1 queries problem
Для Каждого Строка Из Документ.Товары Цикл
    Запрос.УстановитьПараметр("Номенклатура", Строка.Номенклатура);
    Цена = Запрос.Выполнить().Выбрать()[0].Цена;  // Запрос на каждой итерации!
КонецЦикла;
                        """,
                        "good_example": """
// ХОРОШО: Один запрос + временная таблица
Запрос.Текст = "
|ВЫБРАТЬ
|   Номенклатура,
|   Цена
|ИЗ
|   Справочник.Номенклатура
|ГДЕ
|   Номенклатура В (&СписокНоменклатуры)";
   
Запрос.УстановитьПараметр("СписокНоменклатуры", Документ.Товары.ВыгрузитьКолонку("Номенклатура"));
ТаблицаЦен = Запрос.Выполнить().Выгрузить();

Для Каждого Строка Из Документ.Товары Цикл
    НайденнаяЦена = ТаблицаЦен.Найти(Строка.Номенклатура, "Номенклатура");
    Строка.Цена = НайденнаяЦена.Цена;
КонецЦикла;
                        """,
                        "improvement": "N раз ускорение (N = количество строк)",
                        "explanation": "Один запрос вместо N запросов"
                    }
                ]
            },
            
            "transaction_optimization": {
                "title": "Оптимизация транзакций",
                "tips": [
                    "Минимизировать время удержания блокировок",
                    "Использовать управляемые блокировки (УстановитьУправляемуюБлокировку)",
                    "Избегать длинных транзакций",
                    "Commit как можно раньше"
                ]
            },
            
            "memory_optimization": {
                "title": "Оптимизация памяти",
                "tips": [
                    "Очищать большие коллекции после использования (Коллекция.Очистить())",
                    "Использовать выборку вместо выгрузки для больших данных",
                    "Освобождать COM объекты",
                    "Избегать хранения больших объектов в сессии"
                ]
            }
        }
    
    # ==========================================
    # INTEGRATION PATTERNS
    # ==========================================
    
    def _load_integration_patterns(self) -> Dict[str, Any]:
        """Загрузка паттернов интеграции из ИТС"""
        return {
            "rest_api": {
                "name": "REST API интеграция",
                "its_url": "https://its.1c.ru/db/metod8dev/",
                "best_for": ["Синхронные запросы", "Request-Response", "Внешние API"],
                "example_code": """
// HTTP Сервис для REST API
Функция ПолучитьДанныеGET(Запрос)
    
    Ответ = Новый HTTPСервисОтвет(200);
    
    Попытка
        // Получаем параметры
        ID = Запрос.ПараметрыURL.Получить("id");
        
        // Бизнес-логика
        Данные = ПолучитьДанныеПоID(ID);
        
        // JSON ответ
        ОтветJSON = Новый ЗаписьJSON;
        ЗаписатьJSON(ОтветJSON, Данные);
        
        Ответ.УстановитьТелоИзСтроки(ОтветJSON.Закрыть());
        Ответ.Заголовки.Вставить("Content-Type", "application/json");
        
    Исключение
        Ответ = Новый HTTPСервисОтвет(500);
        Ответ.УстановитьТелоИзСтроки(ОписаниеОшибки());
    КонецПопытки;
    
    Возврат Ответ;
    
КонецФункции
                """,
                "security_practices": [
                    "Использовать OAuth2 или API Keys",
                    "Валидация входных данных",
                    "Rate limiting",
                    "HTTPS обязательно",
                    "Логирование всех запросов"
                ]
            },
            
            "message_queue_pattern": {
                "name": "Асинхронный обмен через очереди",
                "best_for": ["Высокая нагрузка", "Decoupling", "Надежность"],
                "patterns": [
                    "Publisher-Subscriber",
                    "Message Queue",
                    "Event Sourcing"
                ],
                "example_workflow": """
1. 1С публикует событие в очередь (Kafka/RabbitMQ)
2. Очередь гарантирует доставку
3. Consumer обрабатывает асинхронно
4. Retry при ошибках
5. Dead Letter Queue для проблемных сообщений
                """
            },
            
            "1c_shina": {
                "name": "1С:Шина данных",
                "its_url": "https://its.1c.ru/db/shina/",
                "best_for": [
                    "Enterprise интеграции",
                    "Трансформация данных",
                    "Маршрутизация сообщений",
                    "Мониторинг обменов"
                ],
                "features": [
                    "Визуальный designer интеграций",
                    "Трансформация форматов",
                    "Мониторинг и логирование",
                    "Обработка ошибок",
                    "Повторная отправка"
                ]
            }
        }
    
    # ==========================================
    # CODE STANDARDS
    # ==========================================
    
    def _load_code_standards(self) -> Dict[str, Any]:
        """Загрузка стандартов кода 1С из ИТС"""
        return {
            "naming_conventions": {
                "functions": {
                    "style": "PascalCase",
                    "examples": {
                        "good": ["ПолучитьДанные", "РассчитатьСумму", "СоздатьДокумент"],
                        "bad": ["получить_данные", "рассчитать_сумму", "создатьДокумент"]
                    }
                },
                "variables": {
                    "style": "PascalCase",
                    "examples": {
                        "good": ["ИмяПользователя", "СуммаДокумента"],
                        "bad": ["имяПользователя", "summa_dokumenta"]
                    }
                },
                "exported_functions": {
                    "naming": "Начинать с действия (глагол)",
                    "examples": ["СоздатьНовыйДокумент", "ПолучитьСписокКонтрагентов"]
                }
            },
            
            "commenting": {
                "mandatory": [
                    "Экспортные функции и процедуры",
                    "Сложная бизнес-логика",
                    "Нестандартные решения"
                ],
                "template": """
// Функция выполняет проверку корректности документа
//
// Параметры:
//   Документ - ДокументСсылка - Проверяемый документ
//   ПолнаяПроверка - Булево - Выполнять полную проверку (по умолчанию Ложь)
//
// Возвращаемое значение:
//   Структура - Результат проверки:
//     * Успех - Булево - Документ корректен
//     * Ошибки - Массив - Список найденных ошибок
//
Функция ПроверитьКорректностьДокумента(Документ, ПолнаяПроверка = Ложь) Экспорт
                """,
                "anti_patterns": [
                    "Закомментированный код (удалять, не комментировать)",
                    "TODO комментарии без срока",
                    "Нерусские комментарии (если проект на русском)"
                ]
            },
            
            "error_handling": {
                "mandatory": "Использовать Попытка...Исключение для критичных операций",
                "example": """
Попытка
    // Критичная операция
    Документ.Записать();
    
Исключение
    // Логирование
    ЗаписьЖурналаРегистрации(
        "Ошибка записи документа",
        УровеньЖурналаРегистрации.Ошибка,
        ,
        Документ,
        ПодробноеПредставлениеОшибки(ИнформацияОбОшибке())
    );
    
    // Информирование пользователя
    ВызватьИсключение "Не удалось записать документ: " + КраткоеПредставлениеОшибки(ИнформацияОбОшибке());
    
КонецПопытки;
                """,
                "best_practices": [
                    "Логировать все исключения",
                    "Информативные сообщения пользователю",
                    "Не скрывать ошибки (пустые Исключение)",
                    "Использовать ПодробноеПредставлениеОшибки для логов"
                ]
            },
            
            "module_structure": {
                "order": [
                    "1. Объявления переменных модуля",
                    "2. Экспортные процедуры и функции",
                    "3. Служебные процедуры и функции"
                ],
                "export_guidelines": [
                    "Экспортировать только публичный API",
                    "Служебные функции НЕ экспортировать",
                    "Документировать все экспортные"
                ]
            }
        }
    
    # ==========================================
    # PUBLIC API
    # ==========================================
    
    async def get_best_practices_for_issue(
        self,
        issue_type: str,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение best practices из ИТС для конкретной проблемы
        
        Args:
            issue_type: "god_object", "slow_query", "coupling", etc.
            context: {"config": "ERP", "module": "Продажи"}
            
        Returns:
            Список релевантных best practices с примерами кода
        """
        logger.info(
            "Getting ITS best practices",
            extra={"issue_type": issue_type}
        )
        
        practices = []
        
        # Маппинг issue types на категории ИТС
        issue_to_category = {
            'god_object': 'architecture',
            'slow_query': 'performance',
            'coupling': 'architecture',
            'circular_dependency': 'architecture',
            'long_method': 'code_quality',
            'copy_paste': 'code_quality'
        }
        
        category = issue_to_category.get(issue_type, 'general')
        
        # Если ИТС доступен - загружаем из него
        if self.its_available and context and context.get('config'):
            try:
                its_docs = await self.its.get_configuration_documentation(
                    context['config']
                )
                
                # Фильтруем practices по категории
                for practice in its_docs.get('best_practices', []):
                    if practice.get('category') == category:
                        practice['source'] = 'ITS (live)'
                        practices.append(practice)
                        
            except Exception as e:
                logger.warning(
                    "Failed to get ITS docs",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "issue_type": issue_type if 'issue_type' in locals() else None
                    }
                )
        
        # Добавляем из встроенной базы знаний
        if issue_type == 'slow_query':
            for tip in self.performance_tips['slow_queries']['tips']:
                practices.append({
                    'title': tip['issue'],
                    'description': tip['explanation'],
                    'bad_example': tip['bad_example'],
                    'good_example': tip['good_example'],
                    'improvement': tip['improvement'],
                    'source': 'ITS (built-in)',
                    'category': 'performance'
                })
        
        # AI ранжирование по релевантности
        for practice in practices:
            practice['relevance_score'] = await self._calculate_relevance(
                practice, issue_type, context or {}
            )
        
        # Сортировка по relevance
        practices.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return practices[:10]  # Top 10
    
    async def _calculate_relevance(
        self,
        practice: Dict,
        issue_type: str,
        context: Dict
    ) -> float:
        """Расчет релевантности practice к issue"""
        # TODO: Использовать embedding similarity
        # Пока упрощенно по keywords
        
        text = f"{practice.get('title', '')} {practice.get('description', '')}".lower()
        
        # Keywords для разных типов проблем
        issue_keywords = {
            'god_object': ['модуль', 'разбиение', 'ответственность', 'srp', 'single'],
            'slow_query': ['запрос', 'производительность', 'индекс', 'оптимизация', 'query'],
            'coupling': ['зависимость', 'связанность', 'интерфейс', 'decoupling'],
            'circular_dependency': ['цикл', 'зависимость', 'событие', 'circular']
        }
        
        keywords = issue_keywords.get(issue_type, [])
        if not keywords:
            return 0.5
        
        matches = sum(1 for kw in keywords if kw in text)
        return min(matches / len(keywords), 1.0)
    
    async def get_architecture_pattern_recommendation(
        self,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Рекомендация архитектурного паттерна из ИТС
        
        Args:
            requirements: {
                "users": 500,
                "load": "high",
                "distributed": True,
                "analytics": False
            }
            
        Returns:
            Рекомендованный паттерн с обоснованием
        """
        # Scoring каждого паттерна
        scores = {}
        
        for pattern_id, pattern in self.architecture_patterns.items():
            score = self._score_architecture_pattern(pattern, requirements)
            scores[pattern_id] = score
        
        # Best pattern
        best_pattern_id = max(scores, key=scores.get)
        best_pattern = self.architecture_patterns[best_pattern_id]
        
        return {
            "recommended_pattern": best_pattern,
            "score": scores[best_pattern_id],
            "rationale": self._explain_pattern_choice(best_pattern, requirements),
            "alternatives": [
                {
                    "pattern": self.architecture_patterns[pid],
                    "score": score
                }
                for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:3]
            ],
            "its_reference": best_pattern['its_url']
        }
    
    def _score_architecture_pattern(
        self,
        pattern: Dict,
        requirements: Dict
    ) -> float:
        """Scoring паттерна под requirements"""
        score = 0.0
        
        # Проверка when_to_use условий
        when_to_use = pattern.get('when_to_use', {})
        
        # Users count
        if 'users' in when_to_use:
            required_users = when_to_use['users']
            actual_users = requirements.get('users', 0)
            
            if '>' in required_users:
                min_users = int(required_users.replace('>', '').strip())
                if actual_users > min_users:
                    score += 2.0
            
        # Load level
        if 'load' in when_to_use:
            required_load = when_to_use['load']
            actual_load = requirements.get('load', 'medium')
            
            if actual_load in required_load:
                score += 2.0
        
        # Best for matching
        best_for = pattern.get('best_for', [])
        requirement_keywords = ' '.join(str(v) for v in requirements.values()).lower()
        
        for bf in best_for:
            if any(word in requirement_keywords for word in bf.lower().split()):
                score += 1.0
        
        return score
    
    def _explain_pattern_choice(
        self,
        pattern: Dict,
        requirements: Dict
    ) -> str:
        """Объяснение выбора паттерна"""
        reasons = []
        
        users = requirements.get('users', 0)
        if users > 100:
            reasons.append(f"Количество пользователей ({users}) требует масштабируемой архитектуры")
        
        if requirements.get('distributed'):
            reasons.append("Требуется распределенная работа")
        
        if requirements.get('load') == 'high':
            reasons.append("Высокая нагрузка требует оптимизации производительности")
        
        return '. '.join(reasons) + '.'
    
    async def check_code_against_standards(
        self,
        code: str,
        module_type: str
    ) -> Dict[str, Any]:
        """
        Проверка кода на соответствие стандартам 1С из ИТС
        
        Args:
            code: BSL код
            module_type: "CommonModule", "ObjectModule", "FormModule"
            
        Returns:
            Отчет о соответствии стандартам
        """
        violations = []
        
        # 1. Проверка именования функций
        import re
        functions = re.findall(r'Функция\s+(\w+)', code)
        
        for func_name in functions:
            # Проверка PascalCase
            if not func_name[0].isupper():
                violations.append({
                    'standard': 'Именование функций',
                    'violation': f"Функция '{func_name}' не в PascalCase",
                    'severity': 'medium',
                    'its_reference': 'https://its.1c.ru/db/metod8dev/',
                    'fix_suggestion': func_name[0].upper() + func_name[1:]
                })
        
        # 2. Проверка комментариев для экспортных функций
        export_functions = re.findall(r'Функция\s+(\w+)\([^)]*\)\s+Экспорт', code)
        
        for func_name in export_functions:
            # Ищем комментарий перед функцией
            func_pattern = f'Функция\\s+{func_name}'
            func_match = re.search(func_pattern, code)
            
            if func_match:
                # Проверяем есть ли комментарий перед
                code_before = code[:func_match.start()]
                lines_before = code_before.split('\n')[-5:]  # 5 строк до функции
                
                has_comment = any('//' in line for line in lines_before)
                
                if not has_comment:
                    violations.append({
                        'standard': 'Комментирование экспортных функций',
                        'violation': f"Функция '{func_name}' (Экспорт) не документирована",
                        'severity': 'high',
                        'its_reference': 'https://its.1c.ru/db/metod8dev/',
                        'fix_suggestion': 'Добавить комментарий с описанием параметров и возвращаемого значения'
                    })
        
        # 3. Проверка обработки ошибок в критичных операциях
        critical_operations = ['Записать', 'Провести', 'ВыполнитьЗапрос', 'HTTPЗапрос']
        
        for operation in critical_operations:
            if operation in code:
                # Проверяем есть ли Попытка...Исключение
                operation_pos = code.find(operation)
                code_around = code[max(0, operation_pos-200):operation_pos+200]
                
                if 'Попытка' not in code_around and 'Исключение' not in code_around:
                    violations.append({
                        'standard': 'Обработка ошибок',
                        'violation': f"Операция '{operation}' без обработки исключений",
                        'severity': 'high',
                        'its_reference': 'https://its.1c.ru/db/metod8dev/',
                        'fix_suggestion': 'Обернуть в Попытка...Исключение с логированием'
                    })
        
        # Расчет compliance score
        total_checks = len(functions) + len(export_functions) + len(critical_operations)
        compliance_score = 1.0 - (len(violations) / max(total_checks, 1))
        
        return {
            "compliance_score": round(compliance_score, 2),
            "total_violations": len(violations),
            "violations": violations,
            "by_severity": self._group_violations_by_severity(violations),
            "recommendations": self._generate_fix_recommendations(violations)
        }
    
    def _group_violations_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Группировка нарушений по severity"""
        from collections import Counter
        severities = [v['severity'] for v in violations]
        return dict(Counter(severities))
    
    def _generate_fix_recommendations(self, violations: List[Dict]) -> List[str]:
        """Генерация рекомендаций по исправлению"""
        recommendations = []
        
        # Группируем по типу
        by_standard = {}
        for v in violations:
            standard = v['standard']
            if standard not in by_standard:
                by_standard[standard] = []
            by_standard[standard].append(v)
        
        # Генерируем рекомендации
        for standard, viols in by_standard.items():
            recommendations.append(
                f"[{viols[0]['severity'].upper()}] Исправить {len(viols)} нарушений: {standard}"
            )
        
        return recommendations


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        integrator = ITSKnowledgeIntegrator()
        
        # Test 1: Best practices for God Object
        print("=== Test 1: Best Practices for God Object ===")
        practices = await integrator.get_best_practices_for_issue(
            "god_object",
            {"config": "ERP"}
        )
        print(f"Found {len(practices)} practices")
        
        # Test 2: Architecture pattern recommendation
        print("\n=== Test 2: Architecture Pattern Recommendation ===")
        pattern = await integrator.get_architecture_pattern_recommendation({
            "users": 500,
            "load": "high",
            "distributed": True
        })
        print(f"Recommended: {pattern['recommended_pattern']['name']}")
        print(f"Score: {pattern['score']}")
        
        # Test 3: Code standards check
        print("\n=== Test 3: Code Standards Check ===")
        test_code = """
Функция получитьДанные()
    Результат = Запрос.Выполнить();
    Возврат Результат;
КонецФункции

Функция СоздатьДокумент() Экспорт
    Документ = Документы.Заказ.СоздатьДокумент();
    Документ.Записать();
    Возврат Документ;
КонецФункции
        """
        
        result = await integrator.check_code_against_standards(test_code, "CommonModule")
        print(f"Compliance score: {result['compliance_score']}")
        print(f"Violations: {result['total_violations']}")
    
    asyncio.run(test())


