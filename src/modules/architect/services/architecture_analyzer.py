"""
Architecture Analyzer Service

Сервис для глубокого анализа архитектуры с расчетом метрик.
"""


from src.modules.architect.domain.exceptions import ArchitectureAnalysisError
from src.modules.architect.domain.models import (
    AntiPattern,
    ArchitectureAnalysisResult,
    ArchitectureMetrics,
    HealthStatus,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ArchitectureAnalyzer:
    """
    Сервис анализа архитектуры

    Features:
    - Coupling analysis
    - Cohesion analysis
    - Cyclic dependencies detection
    - God objects detection
    - Orphan modules detection
    - Overall score calculation
    """

    def __init__(self, anti_pattern_detector=None):
        """
        Args:
            anti_pattern_detector: Детектор anti-patterns
                                  (опционально, для dependency injection)
        """
        if anti_pattern_detector is None:
            from src.modules.architect.services import AntiPatternDetector
            anti_pattern_detector = AntiPatternDetector()

        self.anti_pattern_detector = anti_pattern_detector

    async def analyze_architecture(
        self,
        config_name: str,
        deep_analysis: bool = True
    ) -> ArchitectureAnalysisResult:
        """
        Глубокий анализ архитектуры

        Args:
            config_name: Название конфигурации
            deep_analysis: Глубокий анализ (включая anti-patterns)

        Returns:
            ArchitectureAnalysisResult с метриками и рекомендациями
        """
        try:
            logger.info(
                "Analyzing architecture",
                extra={"config_name": config_name}
            )

            # Calculate metrics
            modules_count = self._get_modules_count(config_name)
            coupling_score = self._analyze_coupling(config_name)
            cohesion_score = self._analyze_cohesion(config_name)
            cyclic_deps = self._find_cyclic_dependencies(config_name)
            god_objects = self._find_god_objects(config_name)
            orphan_modules = self._find_orphan_modules(config_name)

            # Calculate overall score
            overall_score = self._calculate_architecture_score(
                coupling_score,
                cohesion_score,
                len(cyclic_deps),
                len(god_objects)
            )

            metrics = ArchitectureMetrics(
                modules_count=modules_count,
                coupling_score=coupling_score,
                cohesion_score=cohesion_score,
                cyclic_dependencies_count=len(cyclic_deps),
                god_objects_count=len(god_objects),
                orphan_modules_count=len(orphan_modules),
                overall_score=overall_score
            )

            # Detect anti-patterns if deep analysis
            anti_patterns = []
            if deep_analysis:
                anti_patterns = await self.anti_pattern_detector.detect_anti_patterns(
                    config_name
                )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                metrics,
                anti_patterns
            )

            # Determine health status
            health_status = self._get_health_status(overall_score)

            return ArchitectureAnalysisResult(
                metrics=metrics,
                anti_patterns=anti_patterns,
                recommendations=recommendations,
                health_status=health_status
            )

        except Exception as e:
            logger.error("Failed to analyze architecture: %s", e)
            raise ArchitectureAnalysisError(
                f"Failed to analyze architecture: {e}",
                details={"config_name": config_name}
            )

    def _get_modules_count(self, config_name: str) -> int:
        """Подсчет модулей в конфигурации"""
        # Mock implementation
        return 45

    def _analyze_coupling(self, config_name: str) -> float:
        """
        Анализ coupling (связанность модулей)

        Coupling score = количество зависимостей / максимально возможных связей
        Чем ниже, тем лучше (loose coupling)
        """
        # Mock implementation
        # В реальности - запрос к Neo4j Change Graph
        total_dependencies = 150
        max_possible = 45 * 44  # n * (n-1)
        coupling_score = total_dependencies / max_possible
        return round(coupling_score, 2)

    def _analyze_cohesion(self, config_name: str) -> float:
        """
        Анализ cohesion (сплоченность внутри модулей)

        Cohesion score = функции используют общие данные / общее количество функций
        Чем выше, тем лучше (high cohesion)
        """
        # Mock implementation
        return 0.72

    def _find_cyclic_dependencies(self, config_name: str) -> list:
        """Поиск циклических зависимостей"""
        # Mock implementation
        # В реальности - граф-анализ в Neo4j
        return [
            {"cycle": ["ModuleA", "ModuleB", "ModuleC", "ModuleA"]},
            {"cycle": ["ModuleX", "ModuleY", "ModuleX"]}
        ]

    def _find_god_objects(self, config_name: str) -> list:
        """
        Поиск God Objects (модули с слишком многими ответственностями)

        Критерии:
        - Большое количество функций (> 50)
        - Много зависимостей (> 20)
        - Много входящих связей (> 15)
        """
        # Mock implementation
        return [
            {
                "module": "ПродажиСервер",
                "functions_count": 75,
                "dependencies": 25,
                "incoming_links": 18
            }
        ]

    def _find_orphan_modules(self, config_name: str) -> list:
        """Поиск изолированных модулей (нет связей)"""
        # Mock implementation
        return [
            {"module": "УстаревшийМодуль1"},
            {"module": "УстаревшийМодуль2"},
            {"module": "УстаревшийМодуль3"}
        ]

    def _calculate_architecture_score(
        self,
        coupling: float,
        cohesion: float,
        cycles_count: int,
        god_objects_count: int
    ) -> float:
        """
        Расчет общего score архитектуры (1-10)

        10 - идеальная архитектура
        1 - катастрофа
        """
        score = 10.0

        # Penalty for high coupling (0-3 points)
        score -= coupling * 3

        # Bonus for high cohesion (0-2 points)
        score += (cohesion - 0.5) * 2

        # Penalty for cyclic dependencies (0.5 per cycle)
        score -= cycles_count * 0.5

        # Penalty for god objects (1 per object)
        score -= god_objects_count * 1.0

        return max(1.0, min(10.0, round(score, 1)))

    def _get_health_status(self, overall_score: float) -> HealthStatus:
        """Определение статуса здоровья архитектуры"""
        if overall_score >= 9.0:
            return HealthStatus.EXCELLENT
        elif overall_score >= 7.0:
            return HealthStatus.GOOD
        elif overall_score >= 5.0:
            return HealthStatus.ACCEPTABLE
        elif overall_score >= 3.0:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL

    def _generate_recommendations(
        self,
        metrics: ArchitectureMetrics,
        anti_patterns: list[AntiPattern]
    ) -> list[str]:
        """Генерация рекомендаций по улучшению"""
        recommendations = []

        # Coupling recommendations
        if metrics.coupling_score > 0.4:
            recommendations.append(
                f"Уменьшить coupling (текущий: {metrics.coupling_score:.2f}). "
                "Рекомендуется < 0.3"
            )

        # Cohesion recommendations
        if metrics.cohesion_score < 0.6:
            recommendations.append(
                f"Увеличить cohesion (текущий: {metrics.cohesion_score:.2f}). "
                "Рекомендуется > 0.7"
            )

        # Cyclic dependencies
        if metrics.cyclic_dependencies_count > 0:
            recommendations.append(
                f"Устранить {metrics.cyclic_dependencies_count} циклических зависимостей"
            )

        # God objects
        if metrics.god_objects_count > 0:
            recommendations.append(
                f"Рефакторить {metrics.god_objects_count} God Objects. "
                "Разделить на несколько модулей"
            )

        # Orphan modules
        if metrics.orphan_modules_count > 0:
            recommendations.append(
                f"Проверить {metrics.orphan_modules_count} изолированных модулей. "
                "Удалить или интегрировать"
            )

        # Anti-patterns recommendations
        critical_patterns = [
            p for p in anti_patterns
            if p.severity.value in ["critical", "high"]
        ]
        if critical_patterns:
            recommendations.append(
                f"Исправить {len(critical_patterns)} критичных anti-patterns"
            )

        if not recommendations:
            recommendations.append(
                "Архитектура в хорошем состоянии. Поддерживайте качество."
            )

        return recommendations


__all__ = ["ArchitectureAnalyzer"]
