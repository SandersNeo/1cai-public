"""
Dependency Auditor Service

Сервис для аудита зависимостей на уязвимости.
"""

from typing import Dict, List

from src.modules.security.domain.exceptions import DependencyAuditError
from src.modules.security.domain.models import (DependencyAuditResult,
                                                DependencyVulnerability,
                                                RiskLevel, Severity)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class DependencyAuditor:
    """
    Сервис аудита зависимостей

    Features:
    - CVE database check
    - Version comparison
    - Risk assessment
    - Update recommendations
    """

    def __init__(self, patterns_repository=None):
        """
        Args:
            patterns_repository: Repository для CVE data
                                (опционально, для dependency injection)
        """
        if patterns_repository is None:
            from src.modules.security.repositories import \
                SecurityPatternsRepository
            patterns_repository = SecurityPatternsRepository()

        self.patterns_repository = patterns_repository
        self.cve_database = self.patterns_repository.get_cve_database()

    async def audit_dependencies(
        self,
        dependencies: List[Dict[str, str]]
    ) -> DependencyAuditResult:
        """
        Аудит зависимостей на уязвимости

        Args:
            dependencies: Список зависимостей
                         [{"name": "requests", "version": "2.25.0"}, ...]

        Returns:
            DependencyAuditResult
        """
        try:
