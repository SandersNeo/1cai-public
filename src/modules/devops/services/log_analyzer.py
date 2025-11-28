"""
Log Analyzer Service

Сервис для анализа логов с pattern matching и anomaly detection.
Перенесено и рефакторено из devops_agent_extended.py.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.modules.devops.domain.exceptions import LogAnalysisError
from src.modules.devops.domain.models import (
    LogAnalysisResult,
    LogAnomaly,
    LogSeverity,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class LogAnalyzer:
    """
    Сервис анализа логов

    Features:
    - Pattern matching для обнаружения ошибок
    - Anomaly detection
    - Категоризация ошибок
    - Генерация рекомендаций
    """

    def __init__(self, anomaly_detector=None):
        """
        Args:
            anomaly_detector: ML anomaly detector (опционально, для dependency injection)
        """
        self.error_patterns = self._load_error_patterns()
        self.anomaly_threshold = 3.0  # Standard deviations
        self.anomaly_detector = anomaly_detector

    def _load_error_patterns(self) -> List[Dict]:
        """
        База паттернов ошибок

        TODO: Перенести в OptimizationRepository
        """
        return [
            {
                "pattern": r"OutOfMemoryError|MemoryError",
                "category": "memory",
                "severity": "critical",
                "diagnosis": "Memory exhaustion",
            },
            {
                "pattern": r"Connection refused|Connection timeout",
                "category": "network",
                "severity": "high",
                "diagnosis": "Network connectivity issues",
            },
            {
                "pattern": r"Deadlock|Lock wait timeout",
                "category": "database",
                "severity": "critical",
                "diagnosis": "Database lock contention",
            },
            {
                "pattern": r"Permission denied|Access denied",
                "category": "security",
                "severity": "high",
                "diagnosis": "Permission or access control issue",
            },
            {
                "pattern": r"Null pointer|NullPointerException",
                "category": "code",
                "severity": "medium",
                "diagnosis": "Null reference error",
            },
        ]

    async def analyze_logs(
        self, log_file: str, log_type: str = "application"
    ) -> LogAnalysisResult:
        """
        AI анализ логов

        Args:
            log_file: Путь к файлу логов или текст логов
            log_type: Тип логов (application, system, security, audit)

        Returns:
            Результат анализа логов
        """
        logger.info("Analyzing logs", extra={"log_type": log_type})

        try:
            # Read logs
            if Path(log_file).exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()
            else:
                log_content = log_file  # Assume it's the log content itself

            # Parse logs
            errors = []
            warnings = []
            anomalies = []

            # Pattern matching
            for line in log_content.split("\n"):
                # Check error patterns
                for pattern_info in self.error_patterns:
                    if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                        errors.append(
                            {
                                "line": line,
                                "category": pattern_info["category"],
                                "severity": pattern_info["severity"],
                                "diagnosis": pattern_info["diagnosis"],
                            }
                        )

                # Check for warnings
                if re.search(r"WARN|WARNING", line, re.IGNORECASE):
                    warnings.append(line)

            # Detect anomalies (simplified)
            error_rate = len(errors) / max(len(log_content.split("\n")), 1)
            if error_rate > 0.1:  # > 10% error rate
                anomaly = LogAnomaly(
                    type="High error rate",
                    timestamp=datetime.now().isoformat(),
                    severity=LogSeverity.ERROR,
                    metric=f"Error rate: {error_rate:.2%}",
                    possible_cause="System degradation or service outage",
                )
                anomalies.append(anomaly)

            # Pattern analysis
            patterns = self._detect_patterns(errors)

            # Recommendations
            recommendations = self._generate_recommendations(errors, anomalies)

            return LogAnalysisResult(
                summary={
                    "errors_found": len(errors),
                    "warnings_found": len(warnings),
                    "anomalies_found": len(anomalies),
                    "log_type": log_type,
                },
                errors_by_category=self._group_by_category(errors),
                anomalies=anomalies,
                patterns=patterns,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error("Log analysis failed: %s", e)
            raise LogAnalysisError(
                f"Failed to analyze logs: {e}",
                details={"log_type": log_type}
            )

    def _group_by_category(self, errors: List[Dict]) -> Dict[str, int]:
        """Группировка ошибок по категориям"""
        categories = {}
        for error in errors:
            cat = error.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        return categories

    def _detect_patterns(self, errors: List[Dict]) -> List[Dict]:
        """Детекция паттернов в ошибках"""
        patterns = []

        # Group by category
        by_category = self._group_by_category(errors)

        for category, count in by_category.items():
            if count > 10:
                patterns.append(
                    {
                        "pattern": f"High frequency of {category} errors",
                        "count": count,
                        "significance": "high" if count > 50 else "medium",
                    }
                )

        return patterns

    def _generate_recommendations(
        self, errors: List[Dict], anomalies: List[LogAnomaly]
    ) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []

        # Based on errors
        by_category = self._group_by_category(errors)

        if by_category.get("memory", 0) > 5:
            recommendations.append(
                "Investigate memory usage - possible memory leak or insufficient heap size"
            )

        if by_category.get("database", 0) > 10:
            recommendations.append(
                "Review database configuration - high number of database errors detected"
            )

        if by_category.get("network", 0) > 5:
            recommendations.append("Check network connectivity and firewall rules")

        # Based on anomalies
        if len(anomalies) > 0:
            recommendations.append("Set up alerting for error rate > 5%")

        return recommendations


__all__ = ["LogAnalyzer"]
