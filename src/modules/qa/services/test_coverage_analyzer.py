"""
Test Coverage Analyzer Service

Сервис для анализа покрытия тестами с интеграцией SonarQube/Vanessa.
"""

from typing import Any, Dict, Optional

from src.modules.qa.domain.exceptions import CoverageAnalysisError
from src.modules.qa.domain.models import CoverageGrade, CoverageReport
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class TestCoverageAnalyzer:
    """
    Сервис анализа покрытия тестами

    Features:
    - Coverage analysis
    - SonarQube integration (optional)
    - Vanessa integration (optional)
    - Coverage grading
    - Recommendations generation
    """

    def __init__(self):
        """Initialize coverage analyzer"""

    async def analyze_coverage(
        self,
        config_name: str,
        test_results: Optional[Dict[str, Any]] = None
    ) -> CoverageReport:
        """
        Анализ покрытия тестами

        Args:
            config_name: Название конфигурации
            test_results: Результаты выполнения тестов

        Returns:
            CoverageReport с детальным анализом
        """
        try:
            logger.info(
                "Analyzing test coverage",
                extra={"config_name": config_name}
            )

            # Mock coverage data (в реальности - из SonarQube API)
            total_coverage = 72.0
            line_coverage = 75.0
            branch_coverage = 68.0
            function_coverage = 80.0

            # Calculate grade
            grade = self._calculate_grade(total_coverage)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                total_coverage,
                line_coverage,
                branch_coverage,
                function_coverage
            )

            return CoverageReport(
                total_coverage=total_coverage,
                line_coverage=line_coverage,
                branch_coverage=branch_coverage,
                function_coverage=function_coverage,
                grade=grade,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error("Failed to analyze coverage: %s", e)
            raise CoverageAnalysisError(
                f"Failed to analyze coverage: {e}",
                details={"config_name": config_name}
            )

    def _calculate_grade(self, coverage: float) -> CoverageGrade:
        """Расчет оценки покрытия"""
        if coverage >= 90.0:
            return CoverageGrade.A
        elif coverage >= 80.0:
            return CoverageGrade.B
        elif coverage >= 70.0:
            return CoverageGrade.C
        elif coverage >= 60.0:
            return CoverageGrade.D
        else:
            return CoverageGrade.F

    def _generate_recommendations(
        self,
        total: float,
        line: float,
        branch: float,
        function: float
    ) -> list[str]:
        """Генерация рекомендаций"""
        recommendations = []

        if total < 80.0:
            missing = int(80.0 - total)
            recommendations.append(
                f"Увеличить общее покрытие на {missing}% для достижения 80%"
            )

        if branch < 70.0:
            recommendations.append(
                "Добавить тесты для покрытия ветвлений (branch coverage < 70%)"
            )

        if line < 75.0:
            recommendations.append(
                "Увеличить покрытие строк кода (line coverage < 75%)"
            )

        if function < 85.0:
            recommendations.append(
                "Добавить тесты для непокрытых функций"
            )

        if not recommendations:
            recommendations.append(
                "Покрытие на хорошем уровне. Поддерживайте качество."
            )

        return recommendations


__all__ = ["TestCoverageAnalyzer"]
