# [NEXUS IDENTITY] ID: 154764586101082003 | DATE: 2025-11-19

"""
Best Practices Checker
Проверка соответствия best practices 1С
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class BestPracticesChecker:
    """Проверка best practices для 1С разработки"""

    def check(self, code: str, ast: Dict) -> List[Dict]:
        """Полная проверка best practices"""
        issues = []

        issues.extend(self.check_naming_conventions(code, ast))
        issues.extend(self.check_error_handling(code, ast))
        issues.extend(self.check_documentation(code, ast))
        issues.extend(self.check_export_usage(code, ast))

        return issues

    def check_naming_conventions(self, code: str, ast: Dict) -> List[Dict]:
        """Проверка соглашений об именовании"""
        issues = []

        for func in ast.get("functions", []):
            name = func["name"]

            # Правило 1: PascalCase
            if name and not name[0].isupper():
                issues.append(
                    {
                        "type": "NAMING_CONVENTION",
                        "severity": "LOW",
                        "line": func["start_line"],
                        "function": name,
                        "message": f'Имя функции "{name}" должно начинаться с заглавной буквы',
                        "recommendation": f"Переименуйте: {name} → {name[0].upper() + name[1:]}",
                        "standard": "1С:Стандарты разработки, раздел 3.2.1",
                    }
                )

            # Правило 2: Нет транслита
            if self._contains_translit(name):
                issues.append(
                    {
                        "type": "TRANSLIT_IN_NAME",
                        "severity": "MEDIUM",
                        "line": func["start_line"],
                        "function": name,
                        "message": "Используется транслит в имени функции",
                        "recommendation": """
Используйте либо русский, либо английский, но не транслит!

// ❌ Плохо:
Функция PoluchitZnachenie()

// ✅ Хорошо:
Функция ПолучитьЗначение()  // Русский
Функция GetValue()          // Английский
""",
                        "standard": "1С:Стандарты разработки, раздел 3.2.2",
                    }
                )

        return issues

    def check_error_handling(self, code: str, ast: Dict) -> List[Dict]:
        """Проверка обработки ошибок"""
        issues = []

        # Критичные операции без Попытка...Исключение
        critical_operations = [
            ("ВыполнитьЗапрос", "Database query"),
            ("Записать", "Object write"),
            ("Удалить", "Object delete"),
            ("Провести", "Document posting"),
            ("ОтменитьПроведение", "Unpost document"),
        ]

        for func in ast.get("functions", []) + ast.get("procedures", []):
            body = func["body"]

            for operation, description in critical_operations:
                if operation in body and "Попытка" not in body:
                    issues.append(
                        {
                            "type": "MISSING_ERROR_HANDLING",
                            "severity": "HIGH",
                            "function": func["name"],
                            "line": func["start_line"],
                            "operation": operation,
                            "message": f"Операция {operation} без обработки ошибок!",
                            "description": f"""
{description} может вызвать исключение:
- Ошибки БД (connection lost, deadlock)
- Нарушение ссылочной целостности
- Недостаточно прав
- Блокировки объектов

Без обработки ошибок программа "упадет"!
""",
                            "recommendation": """
✅ Оберните в Попытка...Исключение:

Попытка
    Запрос.Выполнить();
Исключение
    ЗаписьЖурналаРегистрации(
        "Ошибка выполнения",
        УровеньЖурналаРегистрации.Ошибка,
        ,
        ,
        ПодробноеПредставлениеОшибки(ИнформацияОбОшибке())
    );

    ВызватьИсключение("Не удалось выполнить операцию");
КонецПопытки;
""",
                            "standard": "1С:Стандарты разработки, раздел 5.3",
                        }
                    )

        return issues

    def check_documentation(self, code: str, ast: Dict) -> List[Dict]:
        """Проверка документации"""
        issues = []

        for func in ast.get("functions", []):
            # Экспортные функции должны быть задокументированы
            if func["is_export"] and not func["has_documentation"]:
                issues.append(
                    {
                        "type": "MISSING_DOCUMENTATION",
                        "severity": "LOW",
                        "line": func["start_line"],
                        "function": func["name"],
                        "message": "Экспортная функция без документации",
                        "recommendation": """
✅ Добавьте документацию в стандартном формате 1С:

// Функция выполняет расчет суммы заказа
//
// Параметры:
//   Заказ - ДокументСсылка.ЗаказПокупателя - Документ заказа
//   СУчетомСкидок - Булево - Учитывать скидки (по умолчанию Истина)
//
// Возвращаемое значение:
//   Число - Сумма заказа
//
// Пример:
//   Сумма = РассчитатьСуммуЗаказа(ТекущийЗаказ, Истина);
//
Функция РассчитатьСуммуЗаказа(Заказ, СУчетомСкидок = Истина) Экспорт
    ...
КонецФункции
""",
                        "standard": "1С:Стандарты разработки, раздел 4.1",
                    }
                )

        return issues

    def check_export_usage(self, code: str, ast: Dict) -> List[Dict]:
        """Проверка использования Экспорт"""
        issues = []

        # Подсчет экспортных функций/процедур
        total_exports = sum(
            1
            for f in ast.get("functions", []) + ast.get("procedures", [])
            if f["is_export"]
        )

        total_items = len(ast.get("functions", [])) + len(ast.get("procedures", []))

        # Если >80% экспортные - возможно злоупотребление
        if total_items > 0 and (total_exports / total_items) > 0.8:
            issues.append(
                {
                    "type": "TOO_MANY_EXPORTS",
                    "severity": "LOW",
                    "message": f"Слишком много экспортных методов ({total_exports}/{total_items})",
                    "recommendation": """
Экспорт следует использовать только для:
- Public API модуля
- Методов, вызываемых из других модулей

Внутренние вспомогательные функции НЕ должны быть экспортными!

Преимущества:
- Меньше coupling
- Проще рефакторинг
- Явный API
""",
                    "standard": "1С:Best Practices",
                }
            )

        return issues

    def _contains_translit(self, text: str) -> bool:
        """Проверка на транслит"""
        # Simplified: если есть и латиница и кириллица
        has_cyrillic = bool(re.search("[а-яА-Я]", text))
        has_latin = bool(re.search("[a-zA-Z]", text))

        return has_cyrillic and has_latin
