"""
Release Notes Generator Service

Сервис для генерации release notes.
"""

from typing import Dict, List

from src.modules.technical_writer.domain.exceptions import \
    ReleaseNotesGenerationError
from src.modules.technical_writer.domain.models import ReleaseNotes
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ReleaseNotesGenerator:
    """
    Сервис генерации release notes

    Features:
    - Conventional Commits parsing
    - Categorization (features, fixes, breaking)
    - Migration guide generation
    """

    async def generate_release_notes(
        self,
        git_commits: List[Dict],
        version: str
    ) -> ReleaseNotes:
        """
        Генерация release notes

        Args:
            git_commits: Список git commits
            version: Версия релиза

        Returns:
            ReleaseNotes
        """
        try:
