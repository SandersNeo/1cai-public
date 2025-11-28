"""
Dependency Auditor Service

Сервис для аудита зависимостей на уязвимости.
"""

from typing import Dict, List

from src.modules.security.domain.exceptions import DependencyAuditError
from src.modules.security.domain.models import (
    DependencyAuditResult,
    DependencyVulnerability,
    RiskLevel,
    Severity,
)
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
            from src.modules.security.repositories import SecurityPatternsRepository
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
            logger.info(
                "Auditing dependencies",
                extra={"count": len(dependencies)}
            )

            vulnerable_deps = []

            for dep in dependencies:
                name = dep.get("name", "")
                version = dep.get("version", "")

                # Check CVE database
                cve_info = self._check_cve(name, version)
                if cve_info:
                    vulnerable_deps.append(
                        DependencyVulnerability(
                            package_name=name,
                            version=version,
                            cve_id=cve_info["cve_id"],
                            severity=Severity(cve_info["severity"]),
                            description=cve_info["description"],
                            fixed_version=cve_info.get("fixed_version")
                        )
                    )

            # Assess risk level
            risk_level = self._assess_risk_level(vulnerable_deps)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                vulnerable_deps
            )

            return DependencyAuditResult(
                total_dependencies=len(dependencies),
                vulnerable_dependencies=vulnerable_deps,
                risk_level=risk_level,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error("Failed to audit dependencies: %s", e)
            raise DependencyAuditError(
                f"Failed to audit dependencies: {e}",
                details={"count": len(dependencies)}
            )

    def _check_cve(self, name: str, version: str) -> dict | None:
        """Проверка CVE database"""
        # Mock implementation
        # В реальности - запрос к CVE API
        key = f"{name}:{version}"
        return self.cve_database.get(key)

    def _assess_risk_level(
        self,
        vulnerable_deps: List[DependencyVulnerability]
    ) -> RiskLevel:
        """Оценка уровня риска"""
        if not vulnerable_deps:
            return RiskLevel.LOW

        # Count by severity
        critical_count = sum(
            1 for d in vulnerable_deps
            if d.severity == Severity.CRITICAL
        )
        high_count = sum(
            1 for d in vulnerable_deps
            if d.severity == Severity.HIGH
        )

        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count > 2:
            return RiskLevel.HIGH
        elif high_count > 0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendations(
        self,
        vulnerable_deps: List[DependencyVulnerability]
    ) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []

        if not vulnerable_deps:
            recommendations.append(
                "All dependencies are up to date. No vulnerabilities found."
            )
            return recommendations

        # Group by severity
        critical_deps = [
            d for d in vulnerable_deps
            if d.severity == Severity.CRITICAL
        ]
        high_deps = [
            d for d in vulnerable_deps
            if d.severity == Severity.HIGH
        ]

        if critical_deps:
            recommendations.append(
                f"CRITICAL: Update {len(critical_deps)} dependencies immediately"
            )
            for dep in critical_deps[:3]:  # Top 3
                if dep.fixed_version:
                    recommendations.append(
                        f"  - {dep.package_name}: {dep.version} → {dep.fixed_version}"
                    )

        if high_deps:
            recommendations.append(
                f"HIGH: Update {len(high_deps)} dependencies soon"
            )

        recommendations.append(
            "Run 'pip-audit' or 'safety check' for detailed analysis"
        )

        return recommendations


__all__ = ["DependencyAuditor"]
