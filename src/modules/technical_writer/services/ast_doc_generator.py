import ast
from typing import List, Dict, Any
from src.modules.technical_writer.domain.models import UserGuide, GuideSection, Audience, FAQItem


from src.infrastructure.event_bus import EventBus, Event, EventType, get_event_bus


class ASTUserGuideGenerator:
    """
    Генерирует руководства пользователя, анализируя исходный код Python с помощью AST.
    Извлекает докстринги, сигнатуры функций и структуру классов.
    """

    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus or get_event_bus()

    async def generate(self, code: str, feature_name: str, audience: Audience) -> UserGuide:
        """
        Генерирует UserGuide из кода.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return self._generate_fallback(feature_name, audience)

        visitor = DocVisitor()
        visitor.visit(tree)

        sections = []

        # 1. Обзор (Докстринг модуля)
        if visitor.module_docstring:
            sections.append(GuideSection(title="Обзор", content=visitor.module_docstring, order=1))

        # 2. Классы / Функции
        for class_info in visitor.classes:
            content = f"### {class_info['name']}\n\n"
            if class_info["docstring"]:
                content += f"{class_info['docstring']}\n\n"

            content += "**Методы:**\n"
            for method in class_info["methods"]:
                content += f"- `{method['name']}{method['args']}`: {method['docstring']}\n"

            sections.append(GuideSection(title=f"Класс: {class_info['name']}", content=content, order=2))

        # 3. Функции (если есть верхнего уровня)
        if visitor.functions:
            content = ""
            for func in visitor.functions:
                content += f"### `{func['name']}{func['args']}`\n"
                content += f"{func['docstring']}\n\n"

            sections.append(GuideSection(title="Вспомогательные функции", content=content, order=3))

        # 4. ЧаВо (Сгенерировано из общих паттернов)
        faq = self._generate_faq(visitor, feature_name)

        # Сборка Markdown
        markdown = self._assemble_markdown(feature_name, sections, faq)

        # Публикация события
        if self.event_bus:
            event = Event(
                type=EventType.DOC_GENERATED,
                payload={"feature": feature_name, "sections_count": len(sections)},
                source="technical_writer",
            )
            await self.event_bus.publish(event)

        return UserGuide(
            feature=feature_name, target_audience=audience, sections=sections, faq=faq, guide_markdown=markdown
        )

    def _generate_fallback(self, feature: str, audience: Audience) -> UserGuide:
        # Фолбэк на простой шаблон, если парсинг кода не удался
        return UserGuide(
            feature=feature,
            target_audience=audience,
            sections=[GuideSection(title="Ошибка", content="Не удалось разобрать код.", order=1)],
            faq=[],
            guide_markdown="# Ошибка\nНе удалось разобрать код.",
        )

    def _generate_faq(self, visitor: "DocVisitor", feature: str) -> List[FAQItem]:
        faq = []
        # Пример эвристики: Если есть __init__, спросить как инициализировать
        for cls in visitor.classes:
            faq.append(
                FAQItem(
                    question=f"Как инициализировать {cls['name']}?",
                    answer=f"Вы можете инициализировать `{cls['name']}` используя его конструктор. См. документацию класса для параметров.",
                )
            )
        return faq

    def _assemble_markdown(self, feature: str, sections: List[GuideSection], faq: List[FAQItem]) -> str:
        md = f"# Руководство пользователя: {feature}\n\n"
        for section in sorted(sections, key=lambda s: s.order):
            md += f"## {section.title}\n\n{section.content}\n\n"

        if faq:
            md += "## ЧаВо\n\n"
            for item in faq:
                md += f"**В: {item.question}**\n\nО: {item.answer}\n\n"
        return md


class DocVisitor(ast.NodeVisitor):
    def __init__(self):
        self.module_docstring = None
        self.classes = []
        self.functions = []

    def visit_Module(self, node: ast.Module):
        self.module_docstring = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_info = {"name": node.name, "docstring": ast.get_docstring(node) or "Нет описания.", "methods": []}

        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.startswith("_") and item.name != "__init__":
                    continue  # Пропускаем приватные методы

                args = [a.arg for a in item.args.args if a.arg != "self"]
                class_info["methods"].append(
                    {
                        "name": item.name,
                        "args": f"({', '.join(args)})",
                        "docstring": ast.get_docstring(item) or "Нет описания.",
                    }
                )

        self.classes.append(class_info)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = [a.arg for a in node.args.args]
        self.functions.append(
            {"name": node.name, "args": f"({', '.join(args)})", "docstring": ast.get_docstring(node) or "Нет описания."}
        )
