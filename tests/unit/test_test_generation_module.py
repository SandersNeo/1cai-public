# [NEXUS IDENTITY] ID: 8078522488586248809 | DATE: 2025-11-19

from typing import Any, Dict, List

import pytest

from src.api import test_generation


def _make_bsl_sample() -> str:
    return """\
// Общий комментарий
#Область СервисныеПроцедуры
Процедура БезЭкспорта(Знач Параметр1, Параметр2 = 42) Экспорт
    Если Параметр2 > 0 Тогда
        Возврат;
    КонецЕсли;
КонецПроцедуры

// Комментарий к функции
Функция ВычислитьЗначение(Знач Параметр3: Число = 0, Параметр4) Экспорт
    Возврат Параметр3 + Параметр4;
КонецФункции
#КонецОбласти
"""


def test_extract_bsl_functions_captures_metadata():
    functions = test_generation.extract_bsl_functions(_make_bsl_sample())

    assert len(functions) == 2
    first, second = functions

    assert first["name"] == "БезЭкспорта"
    assert first["exported"] is True
    assert first["params"][0].endswith("Параметр1")
    assert first["params"][1] == "Параметр2"
    assert first["params_detailed"][1]["default_value"] == "42"
    assert first["region"] == "СервисныеПроцедуры"
    assert "КонецПроцедуры" in first["code"]

    assert second["name"] == "ВычислитьЗначение"
    assert "Параметр3" in second["params_detailed"][0]["name"]
    assert second["params_detailed"][1]["required"] is True
    assert "Комментарий к функции" in second["comments"]


def test_extract_parameters_detailed_complex_signature():
    signature = "Первый: Число = 10, Второй = Неопределено, Третий"

    params = test_generation._extract_parameters_detailed(signature)  # type: ignore[attr-defined]

    assert params == [
        {"name": "Первый", "type": "Число", "default_value": "10", "required": False},
        {
            "name": "Второй",
            "type": None,
            "default_value": "Неопределено",
            "required": False,
        },
        {"name": "Третий", "type": None, "default_value": None, "required": True},
    ]


@pytest.mark.asyncio
async def test_generate_test_cases_with_ai(monkeypatch):
    async def fake_generate_test_cases(*_: Any, **__: Any) -> List[Dict[str, Any]]:
        return [
            {
                "id": "ai-case-1",
                "name": "Positive",
                "description": "AI positive case",
                "input": {"x": 1},
                "expectedOutput": "OK",
                "type": "unit",
                "category": "positive",
            }
        ]

    class FakeAnalyzer:
        async def generate_test_cases(self, **kwargs: Any) -> List[Dict[str, Any]]:
            assert "code" in kwargs and "function_name" in kwargs
            return await fake_generate_test_cases()

    monkeypatch.setattr(
        test_generation,
        "get_openai_analyzer",
        lambda: FakeAnalyzer(),
    )

    func = {
        "name": "TestFunction",
        "code": "Функция TestFunction() КонецФункции",
        "params": [],
    }

    cases = await test_generation.generate_test_cases(func, include_edge_cases=True)

    assert len(cases) == 1
    assert cases[0]["id"] == "ai-case-1"
    assert cases[0]["category"] == "positive"


@pytest.mark.asyncio
async def test_generate_test_cases_fallback(monkeypatch, caplog):
    class FailingAnalyzer:
        async def generate_test_cases(self, **_: Any) -> List[Dict[str, Any]]:
            raise RuntimeError("AI unavailable")

    monkeypatch.setattr(
        test_generation,
        "get_openai_analyzer",
        lambda: FailingAnalyzer(),
    )

    func = {
        "name": "FallbackFunction",
        "code": "Функция FallbackFunction(Знач Аргумент) КонецФункции",
        "params": ["Аргумент"],
    }

    cases = await test_generation.generate_test_cases(func, include_edge_cases=True)

    assert len(cases) == 3  # positive, negative, boundary
    identifiers = {case["id"] for case in cases}
    assert any("boundary" in case_id for case_id in identifiers)
    assert any("negative" in case_id for case_id in identifiers)
    assert "AI генерация тест-кейсов недоступна" in caplog.text


@pytest.mark.asyncio
async def test_generate_bsl_tests_pipeline(monkeypatch):
    async def fake_generate_test_cases(
        func: Dict[str, Any], include_edge_cases: bool
    ) -> List[Dict[str, Any]]:
        assert include_edge_cases is True
        return [
            {
                "id": f"fake-{func['name']}",
                "name": "FakeCase",
                "description": "Generated in test",
                "input": {},
                "expectedOutput": "OK",
                "type": "unit",
                "category": "positive",
            }
        ]

    monkeypatch.setattr(
        test_generation, "generate_test_cases", fake_generate_test_cases
    )

    tests = await test_generation.generate_bsl_tests(_make_bsl_sample())

    assert tests, "Pipeline should produce tests"
    assert tests[0]["framework"] == "xUnitFor1C"
    assert tests[0]["coverage"]["lines"] >= 0
