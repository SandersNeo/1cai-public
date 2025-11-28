"""
GBNF Generator для BSL (1С:Enterprise)

Генерирует GBNF грамматику из правил BSL для использования с llama.cpp.
"""

from typing import List

from bsl_grammar_rules import GRAMMAR_RULES, KEYWORDS, OPERATORS


class GBNFGenerator:
    """Генератор GBNF грамматики для BSL"""

    def __init__(self):
        self.keywords = KEYWORDS
        self.operators = OPERATORS
        self.grammar_rules = GRAMMAR_RULES

    def generate(self) -> str:
        """
        Генерация полной GBNF грамматики

        Returns:
            Строка с GBNF грамматикой
        """
        lines = []

        # Заголовок
        lines.extend(self._generate_header())
        lines.append("")

        # Корневое правило
        lines.append("root ::= file")
        lines.append("")

        # Ключевые слова
        lines.extend(self._generate_keywords())
        lines.append("")

        # Грамматические правила
        lines.extend(self._generate_grammar_rules())
        lines.append("")

        # Базовые токены
        lines.extend(self._generate_basic_tokens())

        return "\n".join(lines)

    def _generate_header(self) -> List[str]:
        """Генерация заголовка"""
        return [
            "# BSL (1С:Enterprise) Grammar for GBNF",
            "# Auto-generated for llama.cpp grammar-constrained generation",
            "# Supports Russian and English keywords",
            "#",
            "# Usage:",
            '#   ./llama-cli --model model.gguf --grammar-file bsl.gbnf --prompt "Создай функцию"',
        ]

    def _generate_keywords(self) -> List[str]:
        """Генерация правил для ключевых слов"""
        lines = ["# Keywords"]

        for key, variants in self.keywords.items():
            # Объединение русских и английских вариантов
            all_variants = []

            if "ru" in variants:
                all_variants.extend(variants["ru"])
            if "en" in variants:
                all_variants.extend(variants["en"])

            # Создание правила
            variants_str = " | ".join(f'"{v}"' for v in all_variants)
            lines.append(f"kw_{key} ::= {variants_str}")

        return lines

    def _generate_grammar_rules(self) -> List[str]:
        """Генерация грамматических правил"""
        lines = ["# Grammar Rules"]

        for rule_name, rule_body in self.grammar_rules.items():
            # Пропускаем правила для базовых токенов (они генерируются отдельно)
            if rule_name in ["identifier", "number", "string"]:
                continue

            # Очистка и форматирование правила
            formatted_rule = self._format_rule(rule_body)
            lines.append(f"{rule_name} ::= {formatted_rule}")

        return lines

    def _format_rule(self, rule: str) -> str:
        """
        Форматирование правила для GBNF

        Преобразует упрощенную BNF в GBNF формат
        """
        # Удаление лишних пробелов и переносов
        rule = " ".join(rule.split())

        # Замена кавычек на правильные для GBNF
        rule = rule.replace("'", '"')

        return rule

    def _generate_basic_tokens(self) -> List[str]:
        """Генерация базовых токенов"""
        return [
            "# Basic Tokens",
            "",
            "# Идентификаторы (поддержка кириллицы)",
            "identifier ::= [a-zA-Zа-яА-ЯёЁ_] [a-zA-Zа-яА-ЯёЁ0-9_]*",
            "",
            "# Числа",
            'number ::= [0-9]+ ("." [0-9]+)?',
            "",
            "# Строки (двойные или одинарные кавычки)",
            'string ::= "\\"" [^\\"]* "\\"" | "\'" [^\']* "\'"',
            "",
            "# Пробелы и комментарии",
            "ws ::= [ \\t\\n\\r]*",
            'comment ::= "//" [^\\n]* | "/*" [^*]* "*/"',
            "",
            "# Экспорт (опциональный)",
            "export ::= kw_export",
        ]

    def save(self, filename: str):
        """
        Сохранение GBNF грамматики в файл

        Args:
            filename: Имя файла для сохранения
        """
        content = self.generate()

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ GBNF grammar saved to {filename}")
        print(f"   Total lines: {len(content.splitlines())}")


def main():
    """Главная функция"""
    print("Generating GBNF grammar for BSL...")

    generator = GBNFGenerator()
    generator.save("bsl.gbnf")

    print("\n✅ Done! Use with llama.cpp:")
    print("   ./llama-cli --model model.gguf --grammar-file bsl.gbnf")


if __name__ == "__main__":
    main()
