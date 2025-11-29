from typing import Dict, Any, Union


class ConditionEvaluator:
    """
    Оценивает условия для управления потоком в сценариях.
    Поддерживает базовые операторы сравнения и логические проверки.
    """

    def evaluate(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Оценивает строку условия относительно текущего контекста.
        Пример условия: "risk_score > 50"
        """
        try:
            # 1. Парсинг условия (Упрощенно: предполагает "ключ оператор значение")
            # Реализация использовала бы правильный парсер выражений или безопасный eval

            parts = condition.split()
            if len(parts) != 3:
                # Может быть проверка булевого флага, например "is_valid"
                if len(parts) == 1:
                    return bool(context.get(parts[0]))
                return False

            left_key, operator, right_val = parts

            left_val = context.get(left_key)

            # Преобразование типов для right_val
            if right_val.isdigit():
                right_val = int(right_val)
            elif right_val.lower() == "true":
                right_val = True
            elif right_val.lower() == "false":
                right_val = False
            elif right_val.startswith("'") and right_val.endswith("'"):
                right_val = right_val[1:-1]

            if operator == "==":
                return left_val == right_val
            elif operator == "!=":
                return left_val != right_val
            elif operator == ">":
                return float(left_val) > float(right_val)
            elif operator == "<":
                return float(left_val) < float(right_val)
            elif operator == ">=":
                return float(left_val) >= float(right_val)
            elif operator == "<=":
                return float(left_val) <= float(right_val)

            return False

        except Exception:
            return False
