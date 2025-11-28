"""
Test Templates Repository

Repository для хранения шаблонов тестов.
"""

from typing import Dict


class TestTemplatesRepository:
    """
    Repository для базы знаний шаблонов тестов

    Хранит:
    - YAxUnit templates
    - Vanessa BDD templates
    - Edge case patterns
    """

    def __init__(self):
        """Initialize repository with default templates"""
        self._test_templates = self._load_test_templates()

    def get_test_templates(self) -> Dict[str, str]:
        """
        Получить все шаблоны тестов

        Returns:
            Словарь шаблонов
        """
        return self._test_templates

    def _load_test_templates(self) -> Dict[str, str]:
        """Load test templates database"""
        return {
            "yaxunit_test": """
// Тест: {test_name}
// Модуль: {module_name}

Процедура {test_name}() Экспорт

    // Arrange (подготовка)
    {arrange_code}

    // Act (действие)
    {act_code}

    // Assert (проверка через YAxUnit)
    {assert_code}

КонецПроцедуры
""",
            "vanessa_bdd": """
# language: ru

Функционал: {feature_name}
    Как {actor}
    Я хочу {action}
    Чтобы {business_value}

Контекст:
    Дано {context}

Сценарий: {scenario_name}
    Когда {when_step}
    Тогда {then_step}
    И {and_step}
""",
            "negative_test": """
Процедура {test_name}_НегативныйТест() Экспорт

    // Тест на обработку {error_case}

    Попытка
        {code_that_should_fail}
        ВызватьИсключение("Ожидалась ошибка");
    Исключение
        // Ожидаемая ошибка
    КонецПопытки;

КонецПроцедуры
""",
        }


__all__ = ["TestTemplatesRepository"]
