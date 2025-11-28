# [NEXUS IDENTITY] ID: 103371612184652594 | DATE: 2025-11-19

"""
Система метрик качества тестов YAxUnit.

Предоставляет:
- Code coverage tracking
- Test effectiveness metrics
- Performance benchmarks
- Quality reports
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


@dataclass
class TestMetrics:
    """Метрики качества тестов"""

    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    execution_time: float = 0.0
    code_coverage: float = 0.0
    branch_coverage: float = 0.0
    test_effectiveness: float = 0.0
    false_positive_rate: float = 0.0
    tests_per_bug: float = 0.0
    timestamp: Optional[str] = None


class TestMetricsCollector:
    """
    Сборщик метрик качества тестов.
    """

    def __init__(self, metrics_dir: Path = Path("output/bsl-tests/metrics")):
        """
        Инициализация сборщика метрик.

        Args:
            metrics_dir: Директория для сохранения метрик
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "TestMetricsCollector initialized",
            extra={"metrics_dir": str(self.metrics_dir)},
        )

    def collect_from_junit_report(
        self,
        report_path: Path,
        execution_time: Optional[float] = None,
    ) -> TestMetrics:
        """
        Собирает метрики из JUnit XML отчета.

        Args:
            report_path: Путь к JUnit XML отчету
            execution_time: Время выполнения тестов (опционально)

        Returns:
            TestMetrics с собранными метриками
        """
        if not report_path.exists():
            logger.warning(
                "JUnit report not found", extra={
                    "report_path": str(report_path)})
            return TestMetrics()

        try:
