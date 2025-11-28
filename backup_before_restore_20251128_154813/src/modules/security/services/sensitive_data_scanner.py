"""
Sensitive Data Scanner Service

Сервис для детекции sensitive data в коде.
"""

import re
from typing import List

from src.modules.security.domain.exceptions import SecretDetectionError
from src.modules.security.domain.models import (Secret, SecretDetectionResult,
                                                SecretType)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class SensitiveDataScanner:
    """
    Сервис детекции sensitive data

    Features:
    - API key detection
    - Password detection
    - Token detection
    - Private key detection
    - Confidence scoring
    """

    def __init__(self, patterns_repository=None):
        """
        Args:
            patterns_repository: Repository для patterns
                                (опционально, для dependency injection)
        """
        if patterns_repository is None:
            from src.modules.security.repositories import \
                SecurityPatternsRepository
            patterns_repository = SecurityPatternsRepository()

        self.patterns_repository = patterns_repository
        self.patterns = (
            self.patterns_repository.get_secret_patterns()
        )

    async def scan_code(self, code: str) -> SecretDetectionResult:
        """
        Сканирование кода на sensitive data

        Args:
            code: Код для сканирования

        Returns:
            SecretDetectionResult
        """
        try:
