# [NEXUS IDENTITY] ID: -581162120877383823 | DATE: 2025-11-19

"""
Performance Analyzer для BSL кода
Детекция проблем производительности
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Анализатор производительности BSL кода"""

    def analyze(self, code: str, ast: Dict) -> List[Dict]:
        """
        Полный анализ производительности

        Returns:
            List of performance issues
        """
        issues = []

        issues.extend(self.detect_n_plus_one_queries(code, ast))
        issues.extend(self.detect_slow_loops(code, ast))
        issues.extend(self.detect_missing_indexes(code))
        issues.extend(self.detect_inefficient_string_ops(code))

        return issues

    def detect_n_plus_one_queries(self, code: str, ast: Dict) -> List[Dict]:
        """Детекция N+1 проблемы"""
        issues = []

        # Проверяем функции и процедуры
        for func in ast.get("functions", []) + ast.get("procedures", []):
            body = func["body"]

            # Паттерн: цикл + запрос внутри
            has_loop = any(
                keyword in body for keyword in ["Для", "Для Каждого", "Пока"]
            )
            has_query = any(
                keyword in body
                for keyword in [
                    "Запрос.Выполнить()",
                    "Выборка.Следующий()",
                    ".Выбрать()",
                ]
            )

            if has_loop and has_query:
                issues.append(
                    {
                        "type": "N_PLUS_ONE_QUERY",
                        "severity": "HIGH",
                        "function": func["name"],
                        "line": func["start_line"],
                        "message": "Обнаружена потенциальная N+1 проблема!",
                        "description": """
N+1 Query Problem - критичная проблема производительности!

Что происходит:
- 1 запрос для получения списка (N записей)
- N запросов для получения деталей каждой записи
- Итого: N+1 запросов вместо 1-2!

Пример:
Если в таблице 1000 записей → 1001 запрос к БД!
Время выполнения: 0.05s × 1000 = 50 секунд!
""",
                        "recommendation": """
✅ Решение: Выполните ОДИН запрос с JOIN или IN:

// ❌ ПЛОХО - N+1 проблема:
Запрос = Новый Запрос;
Запрос.Текст = "ВЫБРАТЬ Ссылка ИЗ Справочник.Контрагенты";
Выборка = Запрос.Выполнить().Выбрать();

Пока Выборка.Следующий() Цикл  // N iterations

    // Запрос внутри цикла!
    ЗапросОстатков = Новый Запрос;
    ЗапросОстатков.Текст = "ВЫБРАТЬ Остаток ГДЕ Контрагент = &Контрагент";
    ЗапросОстатков.УстановитьПараметр("Контрагент", Выборка.Ссылка);
    Остаток = ЗапросОстатков.Выполнить().Выгрузить()[0].Остаток;  // +1 query!

КонецЦикла;

// ✅ ХОРОШО - ОДИН запрос:
Запрос = Новый Запрос;
Запрос.Текст = "
|ВЫБРАТЬ
|    Контрагенты.Ссылка,
|    Контрагенты.Наименование,
|    СУММА(Остатки.Остаток) КАК Остаток
|ИЗ
|    Справочник.Контрагенты КАК Контрагенты
|    ЛЕВОЕ СОЕДИНЕНИЕ РегистрНакопления.Остатки КАК Остатки
|        ПО Контрагенты.Ссылка = Остатки.Контрагент
|СГРУППИРОВАТЬ ПО
|    Контрагенты.Ссылка,
|    Контрагенты.Наименование";

Выборка = Запрос.Выполнить().Выбрать();  // Один запрос для всего!

Пока Выборка.Следующий() Цикл
    // Данные уже есть, без доп. запросов!
    Остаток = Выборка.Остаток;
КонецЦикла;
""",
                        "performance_impact": "10x-100x ускорение",
                        "estimated_speedup": "С 50s до 0.5s",
                    }
                )

        return issues

    def detect_slow_loops(self, code: str, ast: Dict) -> List[Dict]:
        """Детекция медленных операций в циклах"""
        issues = []

        for func in ast.get("functions", []) + ast.get("procedures", []):
            body = func["body"]

            # Паттерн: .Найти() в цикле
            if "Для Каждого" in body and ".Найти(" in body:
                issues.append(
                    {
                        "type": "SLOW_LOOP_SEARCH",
                        "severity": "MEDIUM",
                        "function": func["name"],
                        "line": func["start_line"],
                        "message": "Медленный поиск .Найти() в цикле!",
                        "description": """
Метод .Найти() имеет сложность O(M), где M - размер коллекции.
В цикле с N итерациями → O(N×M) - квадратичная сложность!

Для больших данных это катастрофа:
- 1000 итераций × 1000 элементов = 1,000,000 операций!
""",
                        "recommendation": """
✅ Используйте Соответствие (HashMap) - O(1) lookup:

// ❌ МЕДЛЕННО - O(N×M):
Для Каждого Строка Из ТЧ1 Цикл
    НайденнаяСтрока = ТЧ2.Найти(Строка.Товар, "Товар");  // O(M)
КонецЦикла;

// ✅ БЫСТРО - O(N):
// Сначала создаем индекс
Индекс = Новый Соответствие;
Для Каждого Строка Из ТЧ2 Цикл
    Индекс.Вставить(Строка.Товар, Строка);  // O(1)
КонецЦикла;

// Теперь поиск O(1)
Для Каждого Строка Из ТЧ1 Цикл
    НайденнаяСтрока = Индекс.Получить(Строка.Товар);  // O(1)!
КонецЦикла;
""",
                        "performance_impact": "100x-1000x на больших данных",
                    }
                )

            # Паттерн: СтрЗаменить в цикле (множественные)
            if "Для" in body and body.count("СтрЗаменить") > 3:
                issues.append(
                    {
                        "type": "INEFFICIENT_STRING_OPERATIONS",
                        "severity": "LOW",
                        "function": func["name"],
                        "message": "Множественные СтрЗаменить - используйте регулярные выражения",
                        "recommendation": """
// Вместо множественных СтрЗаменить:
Результат = СтрЗаменить(Строка, "a", "b");
Результат = СтрЗаменить(Результат, "c", "d");
Результат = СтрЗаменить(Результат, "e", "f");

// Используйте один вызов с regex:
Результат = СтрЗаменитьРегВыражением(Строка, "a|c|e", ReplaceFunction);
""",
                    }
                )

        return issues

    def detect_missing_indexes(self, code: str) -> List[Dict]:
        """Детекция запросов без ИНДЕКСИРОВАТЬ ПО"""
        issues = []

        for query in re.finditer(
            r"ВЫБРАТЬ.*?ГДЕ\s+(\w+)\s*=", code, re.IGNORECASE | re.DOTALL
        ):
            query_text = query.group(0)
            field = query.group(1)

            # Проверяем наличие ИНДЕКСИРОВАТЬ ПО
            if "ИНДЕКСИРОВАТЬ" not in query_text.upper():
                line_num = code[: query.start()].count("\n") + 1

                issues.append(
                    {
                        "type": "MISSING_INDEX_HINT",
                        "severity": "MEDIUM",
                        "line": line_num,
                        "field": field,
                        "message": f"Запрос фильтрует по полю {field}, но нет ИНДЕКСИРОВАТЬ ПО",
                        "description": """
ИНДЕКСИРОВАТЬ ПО подсказывает оптимизатору использовать индекс.

Без этого:
- Full table scan (просмотр всей таблицы)
- На больших таблицах - очень медленно
- Блокировки БД
""",
                        "recommendation": f"""
✅ Добавьте ИНДЕКСИРОВАТЬ ПО:

ВЫБРАТЬ ...
ГДЕ {field} = &Параметр

ИНДЕКСИРОВАТЬ ПО {field}  ← Добавьте эту строку!
""",
                        "performance_impact": "3x-10x ускорение на больших таблицах",
                    }
                )

        return issues

    def detect_inefficient_string_ops(self, code: str) -> List[Dict]:
        """Детекция неэффективных строковых операций"""
        issues = []

        # Конкатенация строк в цикле
        if re.search(
            r'Для.*Цикл.*\s+\w+\s*=\s*\w+\s*\+\s*"', code, re.IGNORECASE | re.DOTALL
        ):
            issues.append(
                {
                    "type": "STRING_CONCATENATION_IN_LOOP",
                    "severity": "LOW",
                    "message": "Конкатенация строк в цикле",
                    "recommendation": """
✅ Используйте СтрСоединить или массив:

// ❌ Медленно:
Результат = "";
Для Каждого Элемент Из Массив Цикл
    Результат = Результат + Элемент + ", ";  // Создается новая строка каждый раз!
КонецЦикла;

// ✅ Быстро:
Результат = СтрСоединить(Массив, ", ");
""",
                }
            )

        return issues
