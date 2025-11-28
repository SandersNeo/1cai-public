"""
Optimization Repository

Repository для хранения базы знаний оптимизаций, паттернов ошибок и правил.
"""

from typing import Any, Dict, List


class OptimizationRepository:
    """
    Repository для базы знаний оптимизаций

    Хранит:
    - Pipeline optimizations
    - Error patterns
    - Rightsizing rules
    """

    def __init__(self):
        """Initialize repository with default data"""
        self._pipeline_optimizations = self._load_pipeline_optimizations()
        self._error_patterns = self._load_error_patterns()
        self._rightsizing_rules = self._load_rightsizing_rules()

    def get_pipeline_optimizations(self) -> List[Dict[str, Any]]:
        """
        Получить все оптимизации для CI/CD pipeline

        Returns:
            Список оптимизаций с метаданными
        """
        return self._pipeline_optimizations

    def get_error_patterns(self) -> List[Dict[str, Any]]:
        """
        Получить паттерны ошибок для log analysis

        Returns:
            Список паттернов с regex и категориями
        """
        return self._error_patterns

    def get_rightsizing_rules(self) -> Dict[str, Any]:
        """
        Получить правила для rightsizing

        Returns:
            Правила для CPU/Memory thresholds
        """
        return self._rightsizing_rules

    def _load_pipeline_optimizations(self) -> List[Dict[str, Any]]:
        """Load pipeline optimizations database"""
        return [
            {
                "name": "Docker Layer Caching",
                "stage": "build",
                "description": "Use Docker layer caching to speed up builds",
                "implementation": "Add cache-from and cache-to flags",
                "speedup_range": [0.3, 0.6],
                "effort": "low",
            },
            {
                "name": "Parallel Test Execution",
                "stage": "test",
                "description": "Run tests in parallel to reduce test time",
                "implementation": "pytest -n auto or jest --maxWorkers",
                "speedup_range": [0.4, 0.8],
                "effort": "low",
            },
            {
                "name": "Dependency Caching",
                "stage": "build",
                "description": "Cache dependencies to avoid re-downloading",
                "implementation": "actions/cache for npm/pip/maven",
                "speedup_range": [0.2, 0.5],
                "effort": "low",
            },
            {
                "name": "Incremental Builds",
                "stage": "build",
                "description": "Build only changed modules",
                "implementation": "Gradle/Maven incremental compilation",
                "speedup_range": [0.3, 0.6],
                "effort": "medium",
            },
            {
                "name": "Artifact Caching",
                "stage": "build",
                "description": "Cache build artifacts between runs",
                "implementation": "actions/cache for build outputs",
                "speedup_range": [0.2, 0.5],
                "effort": "low",
            },
            {
                "name": "Matrix Strategy",
                "stage": "test",
                "description": "Run tests for multiple versions in parallel",
                "implementation": "GitHub Actions matrix strategy",
                "speedup_range": [0.3, 0.7],
                "effort": "low",
            },
        ]

    def _load_error_patterns(self) -> List[Dict[str, Any]]:
        """Load error patterns for log analysis"""
        return [
            {
                "category": "memory",
                "patterns": [
                    r"OutOfMemoryError",
                    r"heap space",
                    r"memory leak",
                    r"GC overhead",
                ],
                "severity": "critical",
            },
            {
                "category": "network",
                "patterns": [
                    r"Connection refused",
                    r"timeout",
                    r"DNS resolution failed",
                    r"socket.*closed",
                ],
                "severity": "error",
            },
            {
                "category": "database",
                "patterns": [
                    r"Deadlock",
                    r"lock timeout",
                    r"connection pool",
                    r"too many connections",
                ],
                "severity": "critical",
            },
            {
                "category": "security",
                "patterns": [
                    r"Permission denied",
                    r"authentication failed",
                    r"unauthorized",
                    r"access denied",
                ],
                "severity": "warning",
            },
            {
                "category": "code",
                "patterns": [
                    r"NullPointerException",
                    r"IndexError",
                    r"TypeError",
                    r"AttributeError",
                ],
                "severity": "error",
            },
        ]

    def _load_rightsizing_rules(self) -> Dict[str, Any]:
        """Load rightsizing rules for cost optimization"""
        return {
            "cpu_threshold": 50.0,  # CPU usage < 50% = downsize
            "memory_threshold": 60.0,  # Memory usage < 60% = downsize
            "reserved_instances_threshold": 0.7,  # 70% consistent usage
            "downsize_safety_margin": 1.2,  # 20% safety margin
        }


__all__ = ["OptimizationRepository"]
