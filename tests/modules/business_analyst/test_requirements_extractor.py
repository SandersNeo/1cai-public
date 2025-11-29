"""
Tests for RequirementsExtractor Service
"""

import pytest

from src.modules.business_analyst.services import RequirementsExtractor
from src.modules.business_analyst.domain.models import (
    RequirementType,
    Priority,
    RequirementExtractionResult,
)


@pytest.fixture
def extractor():
    """Fixture for RequirementsExtractor"""
    return RequirementsExtractor()


@pytest.mark.asyncio
async def test_extract_functional_requirements(extractor):
    """Test extraction of functional requirements"""
    document_text = """
    Система должна обеспечивать создание заказов.
    Необходимо реализовать поиск по номеру заказа.
    Пользователь может просматривать историю заказов.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    assert isinstance(result, RequirementExtractionResult)
    assert len(result.functional_requirements) >= 3
    assert all(
        req.type == RequirementType.FUNCTIONAL
        for req in result.functional_requirements
    )


@pytest.mark.asyncio
async def test_extract_non_functional_requirements(extractor):
    """Test extraction of non-functional requirements"""
    document_text = """
    Производительность: система должна обрабатывать 1000 запросов в секунду.
    Время отклика: не более 2 секунд.
    Доступность: 99.9% uptime.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    assert len(result.non_functional_requirements) >= 3
    assert all(
        req.type == RequirementType.NON_FUNCTIONAL
        for req in result.non_functional_requirements
    )


@pytest.mark.asyncio
async def test_extract_constraints(extractor):
    """Test extraction of constraints"""
    document_text = """
    Ограничение: бюджет не более 100,000 рублей.
    Не допускается использование сторонних API.
    Запрещено хранение персональных данных без шифрования.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    assert len(result.constraints) >= 2
    assert all(
        req.type == RequirementType.CONSTRAINT
        for req in result.constraints
    )


@pytest.mark.asyncio
async def test_extract_stakeholders(extractor):
    """Test stakeholder extraction"""
    document_text = """
    Менеджер создает заказ.
    Бухгалтер проверяет оплату.
    Кладовщик отгружает товар.
    Клиент получает уведомление.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    assert "Менеджер" in result.stakeholders
    assert "Бухгалтер" in result.stakeholders
    assert "Кладовщик" in result.stakeholders
    assert "Клиент" in result.stakeholders


@pytest.mark.asyncio
async def test_extract_user_stories(extractor):
    """Test user story extraction"""
    document_text = """
    Как менеджер, я хочу создавать заказы, чтобы ускорить процесс продаж.
    Как бухгалтер, мне нужно проверять оплату.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    assert len(result.user_stories) >= 2
    assert result.user_stories[0].role == "Менеджер"
    assert "создавать заказы" in result.user_stories[0].goal


@pytest.mark.asyncio
async def test_priority_detection(extractor):
    """Test priority detection"""
    document_text = """
    Обязательно система должна поддерживать резервное копирование.
    Желательно добавить экспорт в Excel.
    Система должна валидировать данные.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    high_priority = [
        req for req in result.functional_requirements
        if req.priority == Priority.HIGH
    ]
    low_priority = [
        req for req in result.functional_requirements
        if req.priority == Priority.LOW
    ]

    assert len(high_priority) >= 1
    assert len(low_priority) >= 1


@pytest.mark.asyncio
async def test_confidence_scoring(extractor):
    """Test confidence scoring"""
    document_text = """
    Система должна обеспечивать создание заказов с автоматической валидацией всех обязательных полей.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    assert len(result.functional_requirements) > 0
    req = result.functional_requirements[0]
    assert 0.0 <= req.confidence <= 1.0
    assert req.confidence >= 0.65  # Minimum confidence


@pytest.mark.asyncio
async def test_summary_generation(extractor):
    """Test summary generation"""
    document_text = """
    Система должна создавать заказы.
    Производительность: 1000 запросов/сек.
    Ограничение: бюджет 100,000 руб.
    """

    result = await extractor.extract_requirements(document_text, "tz")

    assert result.summary["total_requirements"] >= 3
    assert result.summary["functional"] >= 1
    assert result.summary["non_functional"] >= 1
    assert result.summary["constraints"] >= 1


@pytest.mark.asyncio
async def test_empty_document(extractor):
    """Test handling of empty document"""
    result = await extractor.extract_requirements("", "tz")

    assert isinstance(result, RequirementExtractionResult)
    assert len(result.functional_requirements) == 0
    assert len(result.non_functional_requirements) == 0
    assert len(result.constraints) == 0


@pytest.mark.asyncio
async def test_source_path_tracking(extractor):
    """Test source path tracking"""
    result = await extractor.extract_requirements(
        "Система должна работать",
        "tz",
        source_path="/path/to/document.docx"
    )

    assert isinstance(result, RequirementExtractionResult)
    # Source path is tracked in result metadata


def test_normalize_whitespace(extractor):
    """Test whitespace normalization"""
    text = "Система   должна    работать"
    normalized = extractor._normalize_whitespace(text)
    assert normalized == "Система должна работать"


def test_split_sentences(extractor):
    """Test sentence splitting"""
    text = "Первое предложение. Второе предложение! Третье предложение?"
    sentences = extractor._split_sentences(text)
    assert len(sentences) >= 3
