"""Severity Estimator Service."""

from ..domain import (
    IssueClassification,
    IssueType,
    SeverityEstimate,
    SeverityFactors,
    SeverityLevel,
)


class SeverityEstimator:
    """Service for estimating issue severity."""

    def estimate_severity(
        self, classification: IssueClassification, factors: SeverityFactors
    ) -> SeverityEstimate:
        """
        Estimate issue severity.

        Args:
            classification: Issue classification
            factors: Severity factors

        Returns:
            Severity estimate
        """
        score = 0.0
        reasoning = []

        # Base score from issue type
        type_scores = {
            IssueType.ERROR: 60,
            IssueType.SECURITY: 80,
            IssueType.PERFORMANCE: 40,
            IssueType.DATABASE: 50,
            IssueType.CONFIGURATION: 30,
            IssueType.WARNING: 20,
            IssueType.NETWORK: 50,
            IssueType.UNKNOWN: 30,
        }

        score = type_scores.get(classification.classified_type, 30)
        reasoning.append(
            f"Base score from {classification.classified_type.value}: {score}"
        )

        # Impact factors
        if factors.affects_production:
            score += 20
            reasoning.append("Affects production: +20")

        if factors.affects_multiple_users:
            score += 15
            reasoning.append("Affects multiple users: +15")

        if factors.data_loss_risk:
            score += 25
            reasoning.append("Data loss risk: +25")

        if factors.security_risk:
            score += 30
            reasoning.append("Security risk: +30")

        # Urgency factors
        if factors.blocks_critical_function:
            score += 20
            reasoning.append("Blocks critical function: +20")

        if not factors.has_workaround:
            score += 10
            reasoning.append("No workaround: +10")

        # Scope factors
        if factors.affected_users_count > 100:
            score += 15
            reasoning.append(f"Affects {factors.affected_users_count} users: +15")
        elif factors.affected_users_count > 10:
            score += 10
            reasoning.append(f"Affects {factors.affected_users_count} users: +10")

        if factors.affected_systems_count > 5:
            score += 10
            reasoning.append(f"Affects {factors.affected_systems_count} systems: +10")

        # Cap score at 100
        score = min(100, score)

        # Determine severity level
        if score >= 80:
            level = SeverityLevel.CRITICAL
        elif score >= 60:
            level = SeverityLevel.HIGH
        elif score >= 40:
            level = SeverityLevel.MEDIUM
        elif score >= 20:
            level = SeverityLevel.LOW
        else:
            level = SeverityLevel.INFO

        # Calculate confidence based on classification confidence
        confidence = classification.confidence * 0.9  # Slightly reduce

        return SeverityEstimate(
            level=level,
            score=score,
            confidence=confidence,
            factors=factors,
            reasoning=reasoning,
        )

    def quick_estimate(
        self, issue_type: IssueType, affects_production: bool = False
    ) -> SeverityLevel:
        """
        Quick severity estimate without full analysis.

        Args:
            issue_type: Type of issue
            affects_production: Whether affects production

        Returns:
            Estimated severity level
        """
        if issue_type == IssueType.SECURITY and affects_production:
            return SeverityLevel.CRITICAL
        elif issue_type == IssueType.ERROR and affects_production:
            return SeverityLevel.HIGH
        elif issue_type == IssueType.PERFORMANCE:
            return SeverityLevel.MEDIUM
        elif issue_type == IssueType.WARNING:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.MEDIUM
