"""
Requirements Extractor Service

Сервис для извлечения требований из документов с NLP и pattern matching.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.modules.business_analyst.domain.exceptions import \
    RequirementExtractionError
from src.modules.business_analyst.domain.models import (
    Priority, Requirement, RequirementExtractionResult, RequirementType,
    UserStory)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class RequirementsExtractor:
    """
    Сервис извлечения требований из документов

    Features:
    - Pattern matching для functional/non-functional/constraints
    - Stakeholder extraction
    - User stories extraction
    - Acceptance criteria extraction
    - Confidence scoring
    """

    def __init__(self, requirements_repository=None):
        """
        Args:
            requirements_repository: Repository для паттернов
                                    (опционально, для dependency injection)
        """
        if requirements_repository is None:
            from src.modules.business_analyst.repositories import \
                RequirementsRepository
            requirements_repository = RequirementsRepository()

        self.requirements_repository = requirements_repository
        self.requirement_patterns = (
            self.requirements_repository.get_requirement_patterns()
        )
        self.user_story_patterns = (
            self.requirements_repository.get_user_story_patterns()
        )

    async def extract_requirements(
        self,
        document_text: str,
        document_type: str = "tz",
        source_path: Optional[str] = None,
    ) -> RequirementExtractionResult:
        """
        Извлечение требований из документа

        Args:
            document_text: Текст документа
            document_type: Тип документа (tz, srs, etc.)
            source_path: Путь к файлу (опционально)

        Returns:
            RequirementExtractionResult с извлеченными требованиями
        """
        try:
