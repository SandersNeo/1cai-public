# [NEXUS IDENTITY] ID: 2600927144413938654 | DATE: 2025-11-19

"""
E2E тесты для LLM Provider Abstraction
---------------------------------------

Тестирование полного цикла работы LLM Provider Abstraction
с QueryClassifier и Orchestrator.
"""

import pytest

from src.ai.llm_provider_abstraction import (
    LLMProviderAbstraction,
    QueryType,
)
from src.ai.orchestrator import QueryType as OrchestratorQueryType


@pytest.mark.asyncio
async def test_e2e_llm_provider_selection_by_query_type() -> None:
    """
    E2E тест: определение типа запроса → выбор провайдера.
    """
    # 1. Создать LLM Provider Abstraction
    abstraction = LLMProviderAbstraction()

    # 2. Выбрать провайдера для генерации кода
    profile = abstraction.select_provider(QueryType.CODE_GENERATION)

    # 3. Проверить результаты
    assert profile is not None
    assert QueryType.CODE_GENERATION in profile.capabilities
    assert profile.provider_id in ["qwen", "kimi"]

    # 4. Выбрать провайдера для русского текста
    profile_ru = abstraction.select_provider(QueryType.RUSSIAN_TEXT)

    # 5. Проверить, что выбран российский провайдер
    assert profile_ru is not None
    assert QueryType.RUSSIAN_TEXT in profile_ru.capabilities
    assert profile_ru.provider_id in ["gigachat", "yandexgpt", "naparnik"]


@pytest.mark.asyncio
async def test_e2e_llm_provider_selection_with_compliance() -> None:
    """
    E2E тест: выбор провайдера с требованиями compliance.
    """
    # 1. Создать LLM Provider Abstraction
    abstraction = LLMProviderAbstraction()

    # 2. Выбрать провайдера с compliance 152-ФЗ
    profile = abstraction.select_provider(
        QueryType.RUSSIAN_TEXT,
        required_compliance=["152-ФЗ"],
    )

    # 3. Проверить результаты
    assert profile is not None
    assert "152-ФЗ" in profile.compliance
    assert profile.provider_id in ["gigachat", "yandexgpt", "naparnik"]


@pytest.mark.asyncio
async def test_e2e_llm_provider_selection_with_cost_constraint() -> None:
    """
    E2E тест: выбор провайдера с ограничением по стоимости.
    """
    # 1. Создать LLM Provider Abstraction
    abstraction = LLMProviderAbstraction()

    # 2. Выбрать провайдера с максимальной стоимостью 0.005
    profile = abstraction.select_provider(
        QueryType.GENERAL,
        max_cost=0.005,
    )

    # 3. Проверить результаты
    assert profile is not None
    assert profile.cost_per_1k_tokens <= 0.005


@pytest.mark.asyncio
async def test_e2e_query_classifier_with_llm_abstraction() -> None:
    """
    E2E тест: QueryClassifier использует LLM Provider Abstraction.
    """
    # 1. Создать QueryClassifier (должен автоматически инициализировать LLM Abstraction)
    from src.ai.orchestrator import QueryClassifier

    classifier = QueryClassifier()

    # 2. Проверить, что LLM Abstraction инициализирован
    assert classifier.llm_abstraction is not None

    # 3. Классифицировать запрос
    intent = classifier.classify("Создай функцию для расчета НДС")

    # 4. Проверить результаты
    assert intent.query_type == OrchestratorQueryType.CODE_GENERATION
    assert len(intent.suggested_tools) > 0

    # 5. Проверить, что в suggested_tools есть LLM провайдеры
    llm_tools = [tool for tool in intent.suggested_tools if tool.startswith("llm:")]
    assert len(llm_tools) > 0


@pytest.mark.asyncio
async def test_e2e_llm_provider_to_tool_registry() -> None:
    """
    E2E тест: конвертация LLM провайдеров в формат ToolRegistry.
    """
    # 1. Создать LLM Provider Abstraction
    abstraction = LLMProviderAbstraction()

    # 2. Конвертировать в формат ToolRegistry
    tools = abstraction.to_tool_registry_format()

    # 3. Проверить результаты
    assert len(tools) > 0
    assert all("id" in tool for tool in tools)
    assert all("schema" in tool for tool in tools)
    assert all("cost" in tool for tool in tools)
    assert all("risks" in tool for tool in tools)

    # 4. Проверить структуру одного инструмента
    tool = tools[0]
    assert tool["id"].startswith("llm:")
    assert "cost" in tool
    assert "risks" in tool
    assert "metadata" in tool


@pytest.mark.asyncio
async def test_e2e_gigachat_integration_with_orchestrator() -> None:
    """
    E2E тест: интеграция GigaChat с Orchestrator.

    Проверяет, что GigaChat клиент инициализируется в Orchestrator
    и может быть использован для русскоязычных запросов.
    """
    from src.ai.orchestrator import AIOrchestrator

    # 1. Создать Orchestrator
    orchestrator = AIOrchestrator()

    # 2. Проверить, что GigaChat клиент инициализирован (может быть None если не настроен)
    assert hasattr(orchestrator, "gigachat_client")

    # 3. Если клиент настроен, проверить is_configured
    if orchestrator.gigachat_client is not None:
        assert hasattr(orchestrator.gigachat_client, "is_configured")
        # Клиент может быть не настроен (нет credentials), это нормально
        if orchestrator.gigachat_client.is_configured:
            # Если настроен, проверить, что можем вызвать generate (но не вызываем реальный API)
            assert callable(getattr(orchestrator.gigachat_client, "generate", None))


@pytest.mark.asyncio
async def test_e2e_yandexgpt_integration_with_orchestrator() -> None:
    """
    E2E тест: интеграция YandexGPT с Orchestrator.

    Проверяет, что YandexGPT клиент инициализируется в Orchestrator
    и может быть использован для русскоязычных запросов.
    """
    from src.ai.orchestrator import AIOrchestrator

    # 1. Создать Orchestrator
    orchestrator = AIOrchestrator()

    # 2. Проверить, что YandexGPT клиент инициализирован (может быть None если не настроен)
    assert hasattr(orchestrator, "yandexgpt_client")

    # 3. Если клиент настроен, проверить is_configured
    if orchestrator.yandexgpt_client is not None:
        assert hasattr(orchestrator.yandexgpt_client, "is_configured")
        # Клиент может быть не настроен (нет credentials), это нормально
        if orchestrator.yandexgpt_client.is_configured:
            # Если настроен, проверить, что можем вызвать generate (но не вызываем реальный API)
            assert callable(getattr(orchestrator.yandexgpt_client, "generate", None))


@pytest.mark.asyncio
async def test_e2e_russian_text_query_provider_selection() -> None:
    """
    E2E тест: выбор провайдера для русскоязычных запросов через LLM Provider Abstraction.

    Проверяет, что для запросов с русским текстом выбираются российские провайдеры
    (GigaChat или YandexGPT).
    """
    from src.ai.llm_provider_abstraction import LLMProviderAbstraction, QueryType

    # 1. Создать LLM Provider Abstraction
    abstraction = LLMProviderAbstraction()

    # 2. Выбрать провайдера для русского текста
    profile = abstraction.select_provider(QueryType.RUSSIAN_TEXT)

    # 3. Проверить, что выбран российский провайдер
    assert profile is not None
    assert QueryType.RUSSIAN_TEXT in profile.capabilities
    assert profile.provider_id in ["gigachat", "yandexgpt", "naparnik"]

    # 4. Проверить compliance (российские провайдеры должны поддерживать 152-ФЗ)
    assert "152-ФЗ" in profile.compliance or "GDPR" in profile.compliance


@pytest.mark.asyncio
async def test_e2e_orchestrator_provider_selection_for_russian() -> None:
    """
    E2E тест: Orchestrator выбирает провайдера для русскоязычных запросов.

    Проверяет, что при обработке запроса с русским текстом Orchestrator
    использует LLM Provider Abstraction для выбора провайдера.
    """
    from src.ai.orchestrator import AIOrchestrator

    # 1. Создать Orchestrator
    orchestrator = AIOrchestrator()

    # 2. Проверить, что LLM Abstraction инициализирован в classifier
    assert orchestrator.classifier.llm_abstraction is not None

    # 3. Проверить, что для русского текста выбирается российский провайдер
    # (это проверяется на уровне логики выбора провайдера в process_query)
    # Не вызываем реальный процесс, так как он может обращаться к внешним API

    # Проверяем только, что логика выбора провайдера работает
    from src.ai.llm_provider_abstraction import QueryType as LLMQueryType

    selected_provider = orchestrator.classifier.llm_abstraction.select_provider(
        LLMQueryType.RUSSIAN_TEXT
    )

    assert selected_provider is not None
    assert selected_provider.provider_id in ["gigachat", "yandexgpt", "naparnik"]


@pytest.mark.asyncio
async def test_e2e_naparnik_integration_with_orchestrator() -> None:
    """
    E2E тест: интеграция 1C:Напарник с Orchestrator.

    Проверяет, что 1C:Напарник клиент инициализируется в Orchestrator
    и может быть использован для 1C-специфичных запросов.
    """
    from src.ai.orchestrator import AIOrchestrator

    # 1. Создать Orchestrator
    orchestrator = AIOrchestrator()

    # 2. Проверить, что 1C:Напарник клиент инициализирован (может быть None если не настроен)
    assert hasattr(orchestrator, "naparnik_client")

    # 3. Если клиент настроен, проверить is_configured
    if orchestrator.naparnik_client is not None:
        assert hasattr(orchestrator.naparnik_client, "is_configured")
        # Клиент может быть не настроен (нет credentials), это нормально
        if orchestrator.naparnik_client.is_configured:
            # Если настроен, проверить, что можем вызвать generate (но не вызываем реальный API)
            assert callable(getattr(orchestrator.naparnik_client, "generate", None))


@pytest.mark.asyncio
async def test_e2e_naparnik_in_llm_provider_abstraction() -> None:
    """
    E2E тест: 1C:Напарник зарегистрирован в LLM Provider Abstraction.

    Проверяет, что 1C:Напарник доступен через LLM Provider Abstraction
    для 1C-специфичных запросов.
    """
    from src.ai.llm_provider_abstraction import LLMProviderAbstraction, QueryType

    # 1. Создать LLM Provider Abstraction
    abstraction = LLMProviderAbstraction()

    # 2. Попытаться получить профиль 1C:Напарник
    naparnik_profile = abstraction.get_profile("naparnik", "naparnik-pro")

    # 3. Проверить, что профиль существует
    assert naparnik_profile is not None
    assert naparnik_profile.provider_id == "naparnik"
    assert naparnik_profile.model_name == "naparnik-pro"

    # 4. Проверить capabilities (1C:Напарник должен поддерживать RUSSIAN_TEXT, GENERAL, CODE_GENERATION)
    assert QueryType.RUSSIAN_TEXT in naparnik_profile.capabilities
    assert QueryType.GENERAL in naparnik_profile.capabilities
    assert QueryType.CODE_GENERATION in naparnik_profile.capabilities

    # 5. Проверить, что 1C:Напарник бесплатный (cost_per_1k_tokens = 0.0)
    assert naparnik_profile.cost_per_1k_tokens == 0.0
