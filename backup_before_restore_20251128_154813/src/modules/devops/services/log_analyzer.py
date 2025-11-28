"""
Log Analyzer Service

Сервис для анализа логов с pattern matching и anomaly detection.
Перенесено и рефакторено из devops_agent_extended.py.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.modules.devops.domain.exceptions import LogAnalysisError
from src.modules.devops.domain.models import (LogAnalysisResult, LogAnomaly,
                                              LogCategory, LogSeverity)
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
