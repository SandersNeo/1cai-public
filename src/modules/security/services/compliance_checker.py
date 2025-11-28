"""
Compliance Checker Service

Сервис для проверки compliance с security frameworks.
"""


from src.modules.security.domain.exceptions import ComplianceCheckError
from src.modules.security.domain.models import (
    ComplianceFramework,
    ComplianceIssue,
    ComplianceReport,
    Severity,
)
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
            from src.modules.security.repositories import SecurityPatternsRepository
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
            logger.info(
                "Checking compliance",
                extra={"framework": framework.value}
            )

            issues = []

            # Get rules for framework
            rules = self.compliance_rules.get(framework.value, [])

            # Check each rule
            for rule in rules:
                if self._check_rule(code, rule):
                    issues.append(
                        ComplianceIssue(
                            framework=framework,
                            rule_id=rule["id"],
                            description=rule["description"],
                            severity=Severity(rule["severity"]),
                            location="code"
                        )
                    )

            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(
                len(rules),
                len(issues)
            )

            # Determine if compliant
            compliant = compliance_score >= 80.0

            return ComplianceReport(
                framework=framework,
                compliant=compliant,
                issues=issues,
                compliance_score=compliance_score
            )

        except Exception as e:
            logger.error("Failed to check compliance: %s", e)
            raise ComplianceCheckError(
                f"Failed to check compliance: {e}",
                details={"framework": framework.value}
            )

    def _check_rule(self, code: str, rule: dict) -> bool:
        """Проверка конкретного правила"""
        # Simplified implementation
        # В реальности - более сложная логика
        pattern = rule.get("pattern", "")
        if not pattern:
            return False

        import re
        return bool(re.search(pattern, code, re.IGNORECASE))

    def _calculate_compliance_score(
        self,
        total_rules: int,
        failed_rules: int
    ) -> float:
        """Расчет compliance score (0-100)"""
        if total_rules == 0:
            return 100.0

        passed_rules = total_rules - failed_rules
        score = (passed_rules / total_rules) * 100.0
        return round(score, 1)


__all__ = ["ComplianceChecker"]
