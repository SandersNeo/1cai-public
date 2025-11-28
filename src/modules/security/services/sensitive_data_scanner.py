"""
Sensitive Data Scanner Service

Сервис для детекции sensitive data в коде.
"""

import re
from typing import List

from src.modules.security.domain.exceptions import SecretDetectionError
from src.modules.security.domain.models import Secret, SecretDetectionResult, SecretType
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
            from src.modules.security.repositories import SecurityPatternsRepository
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
            logger.info("Scanning code for sensitive data")

            secrets = []

            # Detect each type
            for secret_type, pattern_info in self.patterns.items():
                detected = self._detect_type(
                    code,
                    SecretType(secret_type),
                    pattern_info
                )
                secrets.extend(detected)

            # Count high confidence
            high_confidence_count = sum(
                1 for s in secrets if s.confidence > 0.8
            )

            return SecretDetectionResult(
                secrets_found=secrets,
                total_count=len(secrets),
                high_confidence_count=high_confidence_count
            )

        except Exception as e:
            logger.error("Failed to scan sensitive data: %s", e)
            raise SecretDetectionError(
                f"Failed to scan sensitive data: {e}",
                details={}
            )

    def _detect_type(
        self,
        code: str,
        secret_type: SecretType,
        pattern_info: dict
    ) -> List[Secret]:
        """Детекция конкретного типа"""
        secrets = []
        pattern = pattern_info["pattern"]
        confidence = pattern_info["confidence"]

        matches = re.finditer(pattern, code, re.IGNORECASE)

        for match in matches:
            value = match.group(0)
            value_preview = self._mask_value(value)

            secrets.append(
                Secret(
                    type=secret_type,
                    value_preview=value_preview,
                    location="code",
                    line_number=1,
                    confidence=confidence
                )
            )

        return secrets

    def _mask_value(self, value: str) -> str:
        """Маскировка значения"""
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:3]}***{value[-3:]}"


__all__ = ["SensitiveDataScanner"]
