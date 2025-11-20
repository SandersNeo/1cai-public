# [NEXUS IDENTITY] ID: -3636498751512650081 | DATE: 2025-11-19

"""
Tests для AI Code Review Agent
"""

import sys
from pathlib import Path

import pytest

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.agents.code_review.ai_reviewer import AICodeReviewer
from src.ai.agents.code_review.performance_analyzer import PerformanceAnalyzer
from src.ai.agents.code_review.security_scanner import SecurityScanner


@pytest.mark.asyncio
async def test_sql_injection_detection():
    """Test SQL injection detection"""

    scanner = SecurityScanner()

    # Code with SQL injection
    vulnerable_code = """
Функция ПолучитьДанные(Имя)
    Запрос = Новый Запрос;
    Запрос.Текст = "ВЫБРАТЬ * ГДЕ Поле = '" + Имя + "'";
    Возврат Запрос.Выполнить();
КонецФункции
"""

    issues = scanner.scan_sql_injection(vulnerable_code, {})

    assert len(issues) > 0, "Should detect SQL injection"
    assert issues[0]["severity"] == "CRITICAL"
    assert "SQL_INJECTION" in issues[0]["type"]


@pytest.mark.asyncio
async def test_n_plus_one_detection():
    """Test N+1 query detection"""

    analyzer = PerformanceAnalyzer()

    code_with_n_plus_one = """
Функция ПолучитьОстатки(Товары)
    Для Каждого Товар Из Товары Цикл
        Запрос = Новый Запрос;
        Запрос.Выполнить();
    КонецЦикла;
КонецФункции
"""

    ast = {
        "functions": [
            {"name": "ПолучитьОстатки", "body": code_with_n_plus_one, "start_line": 1}
        ]
    }

    issues = analyzer.detect_n_plus_one_queries(code_with_n_plus_one, ast)

    assert len(issues) > 0, "Should detect N+1"
    assert issues[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_full_review():
    """Test полного review"""

    reviewer = AICodeReviewer()

    code = """
Функция РассчитатьСумму(Заказ)
    Сумма = 0;
    Для Каждого Строка Из Заказ.Товары Цикл
        Сумма = Сумма + Строка.Сумма;
    КонецЦикла;
    Возврат Сумма;
КонецФункции
"""

    result = await reviewer.review_code(code, "test.bsl")

    assert "overall_status" in result
    assert "metrics" in result
    assert "issues" in result
    assert result["metrics"]["loc"] > 0


@pytest.mark.asyncio
async def test_good_code_passes():
    """Test что хороший код проходит review"""

    reviewer = AICodeReviewer()

    good_code = """
// Рассчитывает сумму заказа
//
// Параметры:
//   Заказ - ДокументСсылка.ЗаказПокупателя
//
// Возвращаемое значение:
//   Число - Сумма заказа
//
Функция РассчитатьСуммуЗаказа(Заказ) Экспорт

    Попытка
        Запрос = Новый Запрос;
        Запрос.Текст = "
        |ВЫБРАТЬ
        |    СУММА(Сумма) КАК Сумма
        |ИЗ
        |    Документ.ЗаказПокупателя.Товары
        |ГДЕ
        |    Ссылка = &Заказ";

        Запрос.УстановитьПараметр("Заказ", Заказ);

        Результат = Запрос.Выполнить();
        Выборка = Результат.Выбрать();

        Если Выборка.Следующий() Тогда
            Возврат Выборка.Сумма;
        Иначе
            Возврат 0;
        КонецЕсли;

    Исключение
        ЗаписьЖурналаРегистрации("Ошибка", УровеньЖурналаРегистрации.Ошибка);
        Возврат 0;
    КонецПопытки;

КонецФункции
"""

    result = await reviewer.review_code(good_code, "good.bsl")

    # Должно быть мало или 0 critical/high issues
    assert result["metrics"]["critical"] == 0
    assert result["overall_status"] in ["APPROVED", "COMMENTED"]
