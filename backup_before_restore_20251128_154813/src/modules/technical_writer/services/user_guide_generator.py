"""
User Guide Generator Service

Сервис для генерации руководств пользователя.
"""

from typing import List

from src.modules.technical_writer.domain.exceptions import \
    UserGuideGenerationError
from src.modules.technical_writer.domain.models import (Audience, FAQItem,
                                                        GuideSection,
                                                        UserGuide)
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
            from src.modules.technical_writer.repositories import \
                TemplatesRepository
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
