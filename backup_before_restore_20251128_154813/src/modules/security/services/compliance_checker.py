"""
Compliance Checker Service

Сервис для проверки compliance с security frameworks.
"""

from typing import List

from src.modules.security.domain.exceptions import ComplianceCheckError
from src.modules.security.domain.models import (ComplianceFramework,
                                                ComplianceIssue,
                                                ComplianceReport, Severity)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ComplianceChecker:
    """
    Сервис проверки compliance

    Features:
    - OWASP Top 10 validation
    - CWE validation
    - PCI-DSS validation
    - Compliance score calculation
    """

    def __init__(self, patterns_repository=None):
        """
        Args:
            patterns_repository: Repository для compliance rules
                                (опционально, для dependency injection)
        """
        if patterns_repository is None:
            from src.modules.security.repositories import \
                SecurityPatternsRepository
            patterns_repository = SecurityPatternsRepository()

        self.patterns_repository = patterns_repository
        self.compliance_rules = (
            self.patterns_repository.get_compliance_rules()
        )

    async def check_compliance(
        self,
        code: str,
        framework: ComplianceFramework
    ) -> ComplianceReport:
        """
        Проверка compliance с framework

        Args:
            code: Код для проверки
            framework: Compliance framework

        Returns:
            ComplianceReport
        """
        try:
