"""
Anti-Pattern Detector Service

Сервис для детекции anti-patterns в архитектуре.
"""

from typing import List

from src.modules.architect.domain.exceptions import AntiPatternDetectionError
from src.modules.architect.domain.models import (
    AntiPattern,
    AntiPatternType,
    Effort,
    Severity,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class AntiPatternDetector:
    """
    Сервис детекции anti-patterns

    Features:
    - God object detection
    - Circular dependency detection
    - Tight coupling detection
    - Low cohesion detection
    - Refactoring recommendations
    """

    def __init__(self, patterns_repository=None):
        """
        Args:
            patterns_repository: Repository для паттернов
                                (опционально, для dependency injection)
        """
        if patterns_repository is None:
            from src.modules.architect.repositories import (
                ArchitecturePatternsRepository,
            )
            patterns_repository = ArchitecturePatternsRepository()

        self.patterns_repository = patterns_repository
        self.thresholds = self.patterns_repository.get_thresholds()

    async def detect_anti_patterns(
        self,
        config_name: str
    ) -> List[AntiPattern]:
        """
        Детекция anti-patterns в архитектуре

        Args:
            config_name: Название конфигурации

        Returns:
            Список обнаруженных anti-patterns
        """
        try:
            logger.info(
                "Detecting anti-patterns",
                extra={"config_name": config_name}
            )

            anti_patterns = []

            # Detect God Objects
            anti_patterns.extend(self._detect_god_objects(config_name))

            # Detect Circular Dependencies
            anti_patterns.extend(
                self._detect_circular_dependencies(config_name)
            )

            # Detect Tight Coupling
            anti_patterns.extend(self._detect_tight_coupling(config_name))

            # Detect Low Cohesion
            anti_patterns.extend(self._detect_low_cohesion(config_name))

            # Sort by severity
            anti_patterns.sort(
                key=lambda x: {
                    "critical": 0,
                    "high": 1,
                    "medium": 2,
                    "low": 3
                }[x.severity.value]
            )

            return anti_patterns

        except Exception as e:
            logger.error("Failed to detect anti-patterns: %s", e)
            raise AntiPatternDetectionError(
                f"Failed to detect anti-patterns: {e}",
                details={"config_name": config_name}
            )

    def _detect_god_objects(self, config_name: str) -> List[AntiPattern]:
        """Детекция God Objects"""
        # Mock implementation
        # В реальности - анализ через Neo4j
        god_objects = [
            {
                "module": "ПродажиСервер",
                "functions_count": 75,
                "dependencies": 25,
                "incoming_links": 18
            }
        ]

        patterns = []
        for obj in god_objects:
            patterns.append(
                AntiPattern(
                    type=AntiPatternType.GOD_OBJECT,
                    severity=Severity.HIGH,
                    location=obj["module"],
                    metrics={
                        "functions_count": obj["functions_count"],
                        "dependencies": obj["dependencies"],
                        "incoming_links": obj["incoming_links"]
                    },
                    recommendation=(
                        f"Разделить модуль {obj['module']} на несколько "
                        "специализированных модулей по принципу Single Responsibility"
                    ),
                    refactoring_effort=Effort.HIGH,
                    estimated_days=10
                )
            )

        return patterns

    def _detect_circular_dependencies(
        self,
        config_name: str
    ) -> List[AntiPattern]:
        """Детекция циклических зависимостей"""
        # Mock implementation
        cycles = [
            {"cycle": ["ModuleA", "ModuleB", "ModuleC", "ModuleA"]},
            {"cycle": ["ModuleX", "ModuleY", "ModuleX"]}
        ]

        patterns = []
        for cycle in cycles:
            cycle_path = " → ".join(cycle["cycle"])
            patterns.append(
                AntiPattern(
                    type=AntiPatternType.CIRCULAR_DEPENDENCY,
                    severity=Severity.CRITICAL,
                    location=cycle_path,
                    metrics={"cycle_length": len(cycle["cycle"]) - 1},
                    recommendation=(
                        "Разорвать циклическую зависимость через введение "
                        "интерфейса или инверсию зависимости"
                    ),
                    refactoring_effort=Effort.MEDIUM,
                    estimated_days=5
                )
            )

        return patterns

    def _detect_tight_coupling(self, config_name: str) -> List[AntiPattern]:
        """Детекция tight coupling"""
        # Mock implementation
        coupling_score = 0.45  # > threshold 0.3

        if coupling_score > self.thresholds["coupling"]:
            return [
                AntiPattern(
                    type=AntiPatternType.TIGHT_COUPLING,
                    severity=Severity.MEDIUM,
                    location="Вся система",
                    metrics={"coupling_score": coupling_score},
                    recommendation=(
                        "Уменьшить связанность модулей через введение "
                        "слоев абстракции и dependency injection"
                    ),
                    refactoring_effort=Effort.HIGH,
                    estimated_days=15
                )
            ]

        return []

    def _detect_low_cohesion(self, config_name: str) -> List[AntiPattern]:
        """Детекция low cohesion"""
        # Mock implementation
        cohesion_score = 0.55  # < threshold 0.7

        if cohesion_score < self.thresholds["cohesion"]:
            return [
                AntiPattern(
                    type=AntiPatternType.LOW_COHESION,
                    severity=Severity.MEDIUM,
                    location="Несколько модулей",
                    metrics={"cohesion_score": cohesion_score},
                    recommendation=(
                        "Увеличить cohesion через группировку "
                        "связанных функций в одном модуле"
                    ),
                    refactoring_effort=Effort.MEDIUM,
                    estimated_days=7
                )
            ]

        return []


__all__ = ["AntiPatternDetector"]
