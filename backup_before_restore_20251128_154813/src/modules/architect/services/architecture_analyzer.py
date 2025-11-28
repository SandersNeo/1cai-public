"""
Architecture Analyzer Service

Сервис для глубокого анализа архитектуры с расчетом метрик.
"""

from typing import Optional

from src.modules.architect.domain.exceptions import ArchitectureAnalysisError
from src.modules.architect.domain.models import (AntiPattern,
                                                 ArchitectureAnalysisResult,
                                                 ArchitectureMetrics,
                                                 HealthStatus)
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
