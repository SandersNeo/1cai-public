"""
User Guide Generator Service

Сервис для генерации руководств пользователя.
"""

from typing import List

from src.modules.technical_writer.domain.exceptions import UserGuideGenerationError
from src.modules.technical_writer.domain.models import (
    Audience,
    FAQItem,
    GuideSection,
    UserGuide,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class UserGuideGenerator:
    """
    Сервис генерации user guides

    Features:
    - Section generation (audience-specific)
    - FAQ generation
    - Markdown assembly
    """

    def __init__(self, templates_repository=None):
        """
        Args:
            templates_repository: Repository для templates
                                (опционально, для dependency injection)
        """
        if templates_repository is None:
            from src.modules.technical_writer.repositories import TemplatesRepository
            templates_repository = TemplatesRepository()

        self.templates_repository = templates_repository

    async def generate_user_guide(
        self,
        feature: str,
        target_audience: Audience = Audience.END_USER
    ) -> UserGuide:
        """
        Генерация user guide

        Args:
            feature: Название функции/возможности
            target_audience: Целевая аудитория

        Returns:
            UserGuide
        """
        try:
            logger.info(
                "Generating user guide",
                extra={"feature": feature, "audience": target_audience.value}
            )

            # Generate sections
            sections = self._generate_sections(feature, target_audience)

            # Generate FAQ
            faq = self._generate_faq(feature)

            # Assemble guide
            guide_markdown = self._assemble_guide(
                feature,
                sections,
                faq,
                target_audience
            )

            return UserGuide(
                feature=feature,
                target_audience=target_audience,
                sections=sections,
                faq=faq,
                guide_markdown=guide_markdown
            )

        except Exception as e:
            logger.error("Failed to generate user guide: %s", e)
            raise UserGuideGenerationError(
                f"Failed to generate user guide: {e}",
                details={"feature": feature}
            )

    def _generate_sections(
        self,
        feature: str,
        audience: Audience
    ) -> List[GuideSection]:
        """Генерация разделов"""
        sections = [
            GuideSection(
                title="Обзор",
                content=f"Функция '{feature}' предназначена для...",
                order=1
            ),
            GuideSection(
                title="Начало работы",
                content="Для начала работы выполните следующие шаги...",
                order=2
            ),
        ]

        if audience == Audience.END_USER:
            sections.append(
                GuideSection(
                    title="Основные операции",
                    content="### Создание\n...\n\n### Редактирование\n...",
                    order=3
                )
            )
        elif audience == Audience.DEVELOPER:
            sections.append(
                GuideSection(
                    title="API Reference",
                    content="```python\n# Code examples\n```",
                    order=3
                )
            )

        return sections

    def _generate_faq(self, feature: str) -> List[FAQItem]:
        """Генерация FAQ"""
        return [
            FAQItem(
                question=f"Как использовать {feature}?",
                answer="Для использования функции выполните..."
            ),
            FAQItem(
                question="Что делать если возникла ошибка?",
                answer="Проверьте логи и убедитесь что..."
            ),
        ]

    def _assemble_guide(
        self,
        feature: str,
        sections: List[GuideSection],
        faq: List[FAQItem],
        audience: Audience
    ) -> str:
        """Сборка полного руководства"""
        guide = f"# Руководство: {feature}\n\n"
        guide += f"**Аудитория:** {audience.value}\n\n"
        guide += "---\n\n"

        # Sections
        for section in sorted(sections, key=lambda s: s.order):
            guide += f"## {section.title}\n\n"
            guide += f"{section.content}\n\n"

        # FAQ
        guide += "## Часто задаваемые вопросы\n\n"
        for item in faq:
            guide += f"### {item.question}\n\n"
            guide += f"{item.answer}\n\n"

        return guide


__all__ = ["UserGuideGenerator"]
