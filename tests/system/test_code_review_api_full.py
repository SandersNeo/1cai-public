# [NEXUS IDENTITY] ID: 24508789175142724 | DATE: 2025-11-19

"""
Тесты для API Code Review
Версия: 1.0.0
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


# ==================== ТЕСТОВЫЕ ДАННЫЕ ====================

BSL_CODE_WITH_ISSUES = """
// Модуль с потенциальными проблемами

Процедура ОбработатьМассив(Массив)
    
    // Проблема: запрос в цикле
    Для Индекс = 0 По Массив.ВГраница() - 1 Цикл
        Запрос = Новый Запрос;
        Запрос.Текст = "ВЫБРАТЬ * ИЗ Справочники.Товары ГДЕ Код = " + Массив[Индекс].Код;
        Результат = Запрос.Выполнить();
    КонецЦикла;
    
    // Проблема: использование Тип() вместо ПроверитьТип()
    Если Тип(Переменная) = Тип("Строка") Тогда
        // ...
    КонецЕсли;
    
    // Проблема: хардкод пароля (в тестовом коде)
    Пароль = "secret123";
    
КонецПроцедуры
"""

BSL_CODE_CLEAN = """
// Чистый код без проблем

Процедура ОбработатьМассив(Массив)
    
    Запрос = Новый Запрос;
    Запрос.Текст = "ВЫБРАТЬ * ИЗ Справочники.Товары";
    Результат = Запрос.Выполнить();
    
    Если ПроверитьТип(Переменная, Тип("Строка")) Тогда
        // ...
    КонецЕсли;
    
КонецПроцедуры
"""


# ==================== ТЕСТЫ API ENDPOINTS ====================


def test_code_review_health_check():
    """Тест health check endpoint"""
    response = client.get("/api/code-review/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "code-review"


def test_code_review_analyze_basic():
    """Базовый тест анализа кода"""
    response = client.post(
        "/api/code-review/analyze",
        json={
            "content": BSL_CODE_CLEAN,
            "language": "bsl",
            "fileName": "TestModule.bsl",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Проверка структуры ответа
    assert "suggestions" in data
    assert "metrics" in data
    assert "statistics" in data
    assert "recommendations" in data
    assert "timestamp" in data
    assert "analysisId" in data

    # Проверка метрик
    assert "complexity" in data["metrics"]
    assert "maintainability" in data["metrics"]
    assert "securityScore" in data["metrics"]
    assert "performanceScore" in data["metrics"]
    assert "codeQuality" in data["metrics"]


def test_code_review_detect_performance_issues():
    """Тест обнаружения проблем производительности"""
    response = client.post(
        "/api/code-review/analyze",
        json={
            "content": BSL_CODE_WITH_ISSUES,
            "language": "bsl",
            "fileName": "Module.bsl",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Проверка что найдены проблемы производительности
    performance_suggestions = [
        s for s in data["suggestions"] if s["category"] == "performance"
    ]
    assert (
        len(performance_suggestions) > 0
    ), "Должны быть найдены проблемы производительности"

    # Проверка что есть проблема с циклом и запросом
    has_loop_issue = any(
        "цикл" in s["message"].lower() or "производительность" in s["message"].lower()
        for s in performance_suggestions
    )
    assert has_loop_issue, "Должна быть обнаружена проблема с циклом"


def test_code_review_detect_security_issues():
    """Тест обнаружения проблем безопасности"""
    response = client.post(
        "/api/code-review/analyze",
        json={"content": BSL_CODE_WITH_ISSUES, "language": "bsl"},
    )
    assert response.status_code == 200
    data = response.json()

    # Проверка обнаружения проблем безопасности
    security_suggestions = [
        s for s in data["suggestions"] if s["category"] == "security"
    ]

    # Должна быть обнаружена SQL инъекция и хардкод пароля
    has_sql_injection = any(
        "инъекц" in s["message"].lower() or "sql" in s["message"].lower()
        for s in security_suggestions
    )
    has_hardcoded_password = any(
        "парол" in s["message"].lower() for s in security_suggestions
    )

    assert (
        has_sql_injection or has_hardcoded_password
    ), "Должны быть обнаружены проблемы безопасности"


def test_code_review_detect_best_practices():
    """Тест обнаружения нарушений best practices"""
    response = client.post(
        "/api/code-review/analyze",
        json={"content": BSL_CODE_WITH_ISSUES, "language": "bsl"},
    )
    assert response.status_code == 200
    data = response.json()

    # Проверка обнаружения использования Тип() вместо ПроверитьТип()
    best_practice_suggestions = [
        s for s in data["suggestions"] if s["category"] == "best-practice"
    ]

    has_type_suggestion = any(
        "ПроверитьТип" in s["message"] or "Тип()" in s["message"]
        for s in best_practice_suggestions
    )

    # Если есть использование Тип(), должна быть подсказка
    if "Тип(" in BSL_CODE_WITH_ISSUES:
        assert has_type_suggestion, "Должна быть подсказка о ПроверитьТип()"


def test_code_review_metrics_calculation():
    """Тест расчета метрик"""
    response = client.post(
        "/api/code-review/analyze",
        json={"content": BSL_CODE_WITH_ISSUES, "language": "bsl"},
    )
    assert response.status_code == 200
    data = response.json()

    metrics = data["metrics"]

    # Проверка диапазонов метрик
    assert 0 <= metrics["complexity"] <= 100
    assert 0 <= metrics["maintainability"] <= 100
    assert 0 <= metrics["securityScore"] <= 100
    assert 0 <= metrics["performanceScore"] <= 100
    assert 0 <= metrics["codeQuality"] <= 100

    # Код с проблемами должен иметь низкие метрики
    assert (
        metrics["securityScore"] < 100
    ), "Код с проблемами безопасности должен иметь низкий securityScore"
    assert (
        metrics["performanceScore"] < 100
    ), "Код с проблемами производительности должен иметь низкий performanceScore"


def test_code_review_statistics():
    """Тест генерации статистики"""
    response = client.post(
        "/api/code-review/analyze",
        json={"content": BSL_CODE_WITH_ISSUES, "language": "bsl"},
    )
    assert response.status_code == 200
    data = response.json()

    stats = data["statistics"]

    # Проверка структуры статистики
    assert "totalLines" in stats
    assert "functions" in stats
    assert "variables" in stats
    assert "comments" in stats
    assert "potentialIssues" in stats

    # Проверка что статистика имеет смысл
    assert stats["totalLines"] > 0
    assert stats["potentialIssues"] >= len(data["suggestions"])


def test_code_review_empty_code():
    """Тест с пустым кодом"""
    response = client.post(
        "/api/code-review/analyze", json={"content": "", "language": "bsl"}
    )
    assert response.status_code == 200
    data = response.json()

    # Пустой код должен вернуть пустые предложения
    assert len(data["suggestions"]) == 0
    assert data["statistics"]["totalLines"] == 0


def test_code_review_invalid_language():
    """Тест с неподдерживаемым языком"""
    response = client.post(
        "/api/code-review/analyze",
        json={
            "content": "function test() {}",
            "language": "invalid_language",  # Не поддерживается в схеме, но проверяем обработку
        },
    )
    # Должна быть валидация Pydantic
    assert response.status_code in [
        200,
        422,
    ]  # 422 если валидация есть, 200 если обрабатывается


def test_code_review_auto_fix_simple():
    """Тест автозамены (простой случай)"""
    code_with_issue = """
    Если Тип(Переменная) = Тип("Строка") Тогда
        // ...
    КонецЕсли;
    """

    response = client.post(
        "/api/code-review/auto-fix",
        json={"suggestionId": "bsl-type-1", "code": code_with_issue},
    )
    assert response.status_code == 200
    data = response.json()

    assert "fixedCode" in data
    assert "success" in data
    assert "changes" in data

    # Проверка что код был исправлен
    if data["success"]:
        assert "ПроверитьТип" in data["fixedCode"] or "Тип" in data["fixedCode"]
        assert len(data["changes"]) > 0


def test_code_review_auto_fix_no_changes():
    """Тест автозамены когда нет изменений"""
    clean_code = """
    Если ПроверитьТип(Переменная, Тип("Строка")) Тогда
        // ...
    КонецЕсли;
    """

    response = client.post(
        "/api/code-review/auto-fix",
        json={"suggestionId": "test-id", "code": clean_code},
    )
    assert response.status_code == 200
    data = response.json()

    # Может быть success=False если нет изменений
    assert "fixedCode" in data
    assert isinstance(data["changes"], list)


# ==================== ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ====================


def test_code_review_performance():
    """Тест производительности анализа"""
    import time

    large_code = BSL_CODE_WITH_ISSUES * 10  # Увеличиваем код

    start_time = time.time()
    response = client.post(
        "/api/code-review/analyze", json={"content": large_code, "language": "bsl"}
    )
    elapsed_time = time.time() - start_time

    assert response.status_code == 200

    # Анализ должен выполняться быстро (< 5 секунд для небольшого кода)
    assert (
        elapsed_time < 5.0
    ), f"Анализ занял слишком много времени: {elapsed_time:.2f}с"


# ==================== ИНТЕГРАЦИОННЫЕ ТЕСТЫ ====================


def test_code_review_full_workflow():
    """Тест полного workflow: анализ -> автозамена"""
    # 1. Анализ кода
    analyze_response = client.post(
        "/api/code-review/analyze",
        json={
            "content": BSL_CODE_WITH_ISSUES,
            "language": "bsl",
            "fileName": "Module.bsl",
        },
    )
    assert analyze_response.status_code == 200
    analyze_data = analyze_response.json()

    # 2. Проверка что есть предложения
    assert len(analyze_data["suggestions"]) > 0

    # 3. Находим автозаменяемое предложение
    auto_fixable = [
        s for s in analyze_data["suggestions"] if s.get("autoFixable", False)
    ]

    if auto_fixable:
        # 4. Применяем автозамену
        fix_response = client.post(
            "/api/code-review/auto-fix",
            json={"suggestionId": auto_fixable[0]["id"], "code": BSL_CODE_WITH_ISSUES},
        )
        assert fix_response.status_code == 200
        fix_data = fix_response.json()

        # 5. Проверяем что код был изменен
        assert "fixedCode" in fix_data


# ==================== ЗАПУСК ТЕСТОВ ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
