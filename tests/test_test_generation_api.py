# [NEXUS IDENTITY] ID: 8264463485081462481 | DATE: 2025-11-19

"""
Тесты для API Test Generation
Версия: 1.0.0
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


# ==================== ТЕСТОВЫЕ ДАННЫЕ ====================

BSL_FUNCTION_CODE = """
Функция РассчитатьСумму(МассивЧисел)

    Сумма = 0;

    Для Каждого Число Из МассивЧисел Цикл
        Сумма = Сумма + Число;
    КонецЦикла;

    Возврат Сумма;

КонецФункции

Процедура ОбработатьДанные(Данные)

    Если Данные = Неопределено Тогда
        ВызватьИсключение "Данные не определены";
    КонецЕсли;

    // Обработка данных
    Сообщить("Данные обработаны");

КонецПроцедуры
"""

BSL_EMPTY_CODE = ""


# ==================== ТЕСТЫ API ENDPOINTS ====================


def test_test_generation_health_check():
    """Тест health check endpoint"""
    response = client.get("/api/test-generation/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "test-generation"


def test_test_generation_basic():
    """Базовый тест генерации тестов"""
    response = client.post(
        "/api/test-generation/generate",
        json={
            "code": BSL_FUNCTION_CODE,
            "language": "bsl",
            "testType": "unit",
            "includeEdgeCases": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Проверка структуры ответа
    assert "tests" in data
    assert "summary" in data
    assert "timestamp" in data
    assert "generationId" in data

    # Проверка что тесты были сгенерированы
    assert len(data["tests"]) > 0

    # Проверка структуры теста
    test = data["tests"][0]
    assert "id" in test
    assert "functionName" in test
    assert "testCases" in test
    assert "code" in test
    assert "language" in test
    assert "framework" in test
    assert "coverage" in test


def test_test_generation_finds_functions():
    """Тест что функции извлекаются из кода"""
    response = client.post(
        "/api/test-generation/generate",
        json={"code": BSL_FUNCTION_CODE, "language": "bsl", "testType": "unit"},
    )
    assert response.status_code == 200
    data = response.json()

    # Должны быть найдены обе функции
    function_names = [t["functionName"] for t in data["tests"]]

    assert (
        "РассчитатьСумму" in function_names
    ), "Должна быть найдена функция РассчитатьСумму"
    assert (
        "ОбработатьДанные" in function_names
    ), "Должна быть найдена процедура ОбработатьДанные"


def test_test_generation_test_cases():
    """Тест генерации тест-кейсов"""
    response = client.post(
        "/api/test-generation/generate",
        json={
            "code": BSL_FUNCTION_CODE,
            "language": "bsl",
            "testType": "unit",
            "includeEdgeCases": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Проверка что для каждой функции есть тест-кейсы
    for test in data["tests"]:
        assert (
            len(test["testCases"]) > 0
        ), f"Функция {test['functionName']} должна иметь тест-кейсы"

        # Проверка структуры тест-кейса
        test_case = test["testCases"][0]
        assert "id" in test_case
        assert "name" in test_case
        assert "description" in test_case
        assert "input" in test_case
        assert "expectedOutput" in test_case
        assert "type" in test_case
        assert "category" in test_case


def test_test_generation_positive_and_negative_cases():
    """Тест что генерируются положительные и отрицательные тест-кейсы"""
    response = client.post(
        "/api/test-generation/generate",
        json={
            "code": BSL_FUNCTION_CODE,
            "language": "bsl",
            "testType": "unit",
            "includeEdgeCases": True,
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Проверка наличия разных типов тест-кейсов
    all_categories = []
    for test in data["tests"]:
        for test_case in test["testCases"]:
            all_categories.append(test_case["category"])

    # Должны быть хотя бы positive тест-кейсы
    assert "positive" in all_categories, "Должны быть положительные тест-кейсы"

    # Если функция принимает параметры, должны быть negative тест-кейсы
    has_negative = "negative" in all_categories
    has_params = any(
        len(test["testCases"]) > 0 and test["testCases"][0].get("input", {})
        for test in data["tests"]
    )

    if has_params:
        assert (
            has_negative or "boundary" in all_categories
        ), "Для функций с параметрами должны быть negative/boundary тесты"


def test_test_generation_test_code_format():
    """Тест формата сгенерированного кода тестов"""
    response = client.post(
        "/api/test-generation/generate",
        json={"code": BSL_FUNCTION_CODE, "language": "bsl", "testType": "unit"},
    )
    assert response.status_code == 200
    data = response.json()

    for test in data["tests"]:
        test_code = test["code"]

        # Проверка что код содержит основные элементы
        assert (
            "Процедура" in test_code or "Функция" in test_code
        ), "Тестовый код должен содержать процедуру/функцию"
        assert (
            test["functionName"] in test_code
        ), f"Код должен содержать имя функции {test['functionName']}"

        # Проверка что код на BSL (содержит типичные конструкции)
        assert "КонецПроцедуры" in test_code or "КонецФункции" in test_code


def test_test_generation_coverage_metrics():
    """Тест расчета метрик покрытия"""
    response = client.post(
        "/api/test-generation/generate",
        json={"code": BSL_FUNCTION_CODE, "language": "bsl", "testType": "unit"},
    )
    assert response.status_code == 200
    data = response.json()

    for test in data["tests"]:
        coverage = test["coverage"]

        # Проверка структуры покрытия
        assert "lines" in coverage
        assert "branches" in coverage
        assert "functions" in coverage

        # Проверка диапазонов
        assert 0 <= coverage["lines"] <= 100
        assert 0 <= coverage["branches"] <= 100
        assert coverage["functions"] >= 1, "Должна быть покрыта минимум 1 функция"


def test_test_generation_summary():
    """Тест генерации summary"""
    response = client.post(
        "/api/test-generation/generate",
        json={"code": BSL_FUNCTION_CODE, "language": "bsl", "testType": "unit"},
    )
    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]

    # Проверка структуры summary
    assert "totalTests" in summary
    assert "totalTestCases" in summary
    assert "totalFunctions" in summary
    assert "averageCoverage" in summary
    assert "language" in summary

    # Проверка значений
    assert summary["totalTests"] > 0
    assert summary["totalTestCases"] > 0
    assert summary["totalFunctions"] > 0
    assert summary["language"] == "bsl"
    assert 0 <= summary["averageCoverage"] <= 100


def test_test_generation_empty_code():
    """Тест с пустым кодом"""
    response = client.post(
        "/api/test-generation/generate",
        json={"code": BSL_EMPTY_CODE, "language": "bsl", "testType": "unit"},
    )
    assert response.status_code == 200
    data = response.json()

    # Для пустого кода не должно быть тестов
    assert len(data["tests"]) == 0
    assert data["summary"]["totalTests"] == 0


def test_test_generation_specific_function():
    """Тест генерации тестов для конкретной функции"""
    response = client.post(
        "/api/test-generation/generate",
        json={
            "code": BSL_FUNCTION_CODE,
            "language": "bsl",
            "functionName": "РассчитатьСумму",
            "testType": "unit",
        },
    )
    assert response.status_code == 200
    data = response.json()

    # Если указана конкретная функция, должны быть тесты только для неё
    # (или для всех если фильтрация не реализована)
    function_names = [t["functionName"] for t in data["tests"]]

    # Должна быть функция РассчитатьСумму в результатах
    assert "РассчитатьСумму" in function_names


def test_test_generation_unsupported_language():
    """Тест с неподдерживаемым языком"""
    response = client.post(
        "/api/test-generation/generate",
        json={
            "code": "function test() {}",
            "language": "typescript",  # Пока не поддерживается
            "testType": "unit",
        },
    )

    # Должна быть ошибка или пустой результат
    assert response.status_code in [200, 400]

    if response.status_code == 400:
        assert "не поддерживается" in response.json()["detail"].lower()


def test_test_generation_different_test_types():
    """Тест генерации разных типов тестов"""
    for test_type in ["unit", "integration", "e2e"]:
        response = client.post(
            "/api/test-generation/generate",
            json={"code": BSL_FUNCTION_CODE, "language": "bsl", "testType": test_type},
        )
        assert response.status_code == 200

        # unit тесты должны работать всегда
        if test_type == "unit":
            data = response.json()
            assert len(data["tests"]) > 0


# ==================== ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ====================


def test_test_generation_performance():
    """Тест производительности генерации тестов"""
    import time

    large_code = BSL_FUNCTION_CODE * 5  # Увеличиваем код

    start_time = time.time()
    response = client.post(
        "/api/test-generation/generate",
        json={"code": large_code, "language": "bsl", "testType": "unit"},
    )
    elapsed_time = time.time() - start_time

    assert response.status_code == 200

    # Генерация должна выполняться быстро (< 10 секунд)
    assert (
        elapsed_time < 10.0
    ), f"Генерация заняла слишком много времени: {elapsed_time:.2f}с"


# ==================== ЗАПУСК ТЕСТОВ ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
