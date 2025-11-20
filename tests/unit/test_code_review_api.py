# [NEXUS IDENTITY] ID: 6336601157625769646 | DATE: 2025-11-19

import pytest
from fastapi.testclient import TestClient

from src.api.code_review import (AutoFixRequest, analyze_bsl_code,
                                 auto_fix_code, router)
from src.main import \
    app as fastapi_app  # Assuming router already included in app
from src.services import caching_service
from src.services.openai_code_analyzer import (OpenAICodeAnalyzer,
                                               set_openai_analyzer)

# Ensure router is mounted (in case tests import module directly)
if router not in fastapi_app.routes:
    fastapi_app.include_router(router)

client = TestClient(fastapi_app)
pytestmark = pytest.mark.timeout(10)


@pytest.fixture(autouse=True)
def reset_openai_analyzer():
    set_openai_analyzer(OpenAICodeAnalyzer())
    yield
    set_openai_analyzer(OpenAICodeAnalyzer())


@pytest.fixture(autouse=True)
def reset_cache():
    caching_service.memory_cache.clear()
    caching_service.memory_cache_ttl.clear()
    caching_service._cache_service = None


def test_analyze_bsl_code_empty():
    result = analyze_bsl_code("")
    assert result["metrics"]["maintainability"] == 100
    assert result["statistics"]["totalLines"] == 0
    assert result["recommendations"] == []


def test_analyze_bsl_code_detects_issues():
    code = """
Процедура Тест()
    Пароль = "secret";
    Для Каждого Строка По Справочники.Номенклатура Цикл
        Запрос = "ВЫБРАТЬ *" + Переменная;
    КонецЦикла;
КонецПроцедуры
"""
    result = analyze_bsl_code(code)
    categories = {s["category"] for s in result["suggestions"]}
    assert {"security", "performance"}.issubset(categories)
    assert result["statistics"]["totalLines"] > 0


def test_analyze_code_endpoint_without_ai(monkeypatch):
    payload = {
        "content": "Процедура ТестAI() КонецПроцедуры",
        "language": "bsl",
    }

    response = client.post("/api/code-review/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["analysisId"].startswith("analysis-")
    assert "metrics" in data
    assert "statistics" in data


def test_analyze_code_endpoint_with_ai(monkeypatch):
    class DummyAnalyzer:
        def __init__(self):
            self.enabled = True
            self.model = "dummy"

        async def analyze_code(self, *args, **kwargs):
            return [
                {
                    "id": "ai-1",
                    "type": "info",
                    "severity": "low",
                    "message": "AI",
                    "description": "AI suggestion",
                    "suggestion": None,
                    "code": None,
                    "position": {"line": 1, "column": 1},
                    "category": "style",
                    "autoFixable": False,
                    "confidence": 0.5,
                }
            ]

    set_openai_analyzer(DummyAnalyzer())

    payload = {
        "content": "Процедура Тест() КонецПроцедуры",
        "language": "bsl",
    }

    response = client.post("/api/code-review/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any(s["id"] == "ai-1" for s in data["suggestions"])


@pytest.mark.asyncio
async def test_auto_fix_code_type_check():
    request = AutoFixRequest(
        suggestionId="type-check",
        code="Если Тип(Значение) = Строка Тогда КонецЕсли;",
    )
    result = await auto_fix_code(request)
    assert result.success
    assert "ПроверитьТип(" in result.fixedCode


@pytest.mark.asyncio
async def test_auto_fix_code_error_handling():
    request = AutoFixRequest(
        suggestionId="error-handling",
        code='Сообщить("Ошибка");',
    )
    result = await auto_fix_code(request)
    assert result.success
    assert "Попытка" in result.fixedCode
    assert "Исключение" in result.fixedCode


@pytest.mark.asyncio
async def test_auto_fix_code_magic_number():
    request = AutoFixRequest(
        suggestionId="magic-number",
        code="Если Значение = 123 Тогда КонецЕсли;",
    )
    result = await auto_fix_code(request)
    assert result.success
    assert "КОНСТАНТА_123" in result.fixedCode
