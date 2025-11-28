"""
Pipeline Optimizer Service

Сервис для оптимизации CI/CD pipelines согласно Clean Architecture.
Перенесено и рефакторено из devops_agent_extended.py.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from src.modules.devops.domain.exceptions import PipelineOptimizationError
from src.modules.devops.domain.models import (
    OptimizationEffort,
    PipelineConfig,
    PipelineMetrics,
    PipelineOptimization,
    PipelineStage,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class PipelineOptimizer:
    """
    Сервис оптимизации CI/CD pipeline

    Features:
    - Анализ pipeline метрик
    - Рекомендации по оптимизации
    - Генерация оптимизированного pipeline config
    - Health score calculation
    """

    def __init__(self, optimizations_repository=None):
        """
        Args:
            optimizations_repository: Repository для базы знаний оптимизаций
                                     (опционально, для dependency injection)
        """
        if optimizations_repository is None:
            from src.modules.devops.repositories import OptimizationRepository
            optimizations_repository = OptimizationRepository()

        self.optimizations_repository = optimizations_repository
        self.optimizations_db = (
            self.optimizations_repository.get_pipeline_optimizations()
        )

    async def analyze_pipeline(
        self,
        pipeline_config: PipelineConfig,
        metrics: Optional[PipelineMetrics] = None
    ) -> Dict[str, Any]:
        """
        Анализ CI/CD pipeline

        Args:
            pipeline_config: Конфигурация pipeline
            metrics: Метрики выполнения

        Returns:
            Детальный анализ с рекомендациями
        """
        logger.info(
            "Analyzing CI/CD pipeline",
            extra={"pipeline": pipeline_config.name}
        )

        # Use default metrics if not provided
        if metrics is None:
            metrics = PipelineMetrics(
                total_duration=1500,  # 25 min
                build_time=300,  # 5 min
                test_time=900,  # 15 min
                deploy_time=300,  # 5 min
            )

        # Analyze stages
        stages_analysis = {}

        # Build stage
        if metrics.build_time and metrics.build_time > 180:  # > 3 min
            stages_analysis["build"] = {
                "status": "needs_optimization",
                "current_time": metrics.build_time,
                "issues": [
                    "Build time exceeds 3 minutes",
                    "Possible lack of caching",
                    "Docker layers not optimized",
                ],
            }

        # Test stage
        if metrics.test_time and metrics.test_time > 600:  # > 10 min
            stages_analysis["test"] = {
                "status": "needs_optimization",
                "current_time": metrics.test_time,
                "issues": [
                    "Test time exceeds 10 minutes",
                    "Tests not running in parallel",
                    "Possible slow integration tests",
                ],
            }

        # Deploy stage
        if metrics.deploy_time and metrics.deploy_time > 240:  # > 4 min
            stages_analysis["deploy"] = {
                "status": "needs_optimization",
                "current_time": metrics.deploy_time,
                "issues": [
                    "Deploy time exceeds 4 minutes",
                    "Possible inefficient deployment strategy",
                ],
            }

        return {
            "current_metrics": metrics.model_dump(),
            "stages_analysis": stages_analysis,
            "overall_health": self._calculate_health_score(metrics),
            "timestamp": datetime.now().isoformat(),
        }

    async def recommend_optimizations(
        self,
        pipeline_config: PipelineConfig,
        metrics: PipelineMetrics
    ) -> List[PipelineOptimization]:
        """
        Рекомендации по оптимизации

        Args:
            pipeline_config: Конфигурация pipeline
            metrics: Метрики выполнения

        Returns:
            Список рекомендаций с ожидаемым эффектом
        """
        recommendations = []

        # Analyze current pipeline
        analysis = await self.analyze_pipeline(pipeline_config, metrics)

        # Match optimizations to problems
        for opt in self.optimizations_db:
            stage = opt["stage"]

            # Check if this stage needs optimization
            if stage == "all" or stage in analysis["stages_analysis"]:
                speedup_min, speedup_max = opt["speedup_range"]
                avg_speedup = (speedup_min + speedup_max) / 2

                optimization = PipelineOptimization(
                    optimization=opt["name"],
                    stage=PipelineStage(stage),
                    description=opt["description"],
                    implementation=opt["implementation"],
                    expected_speedup_percent=int(avg_speedup * 100),
                    effort=OptimizationEffort(opt["effort"]),
                    priority=self._calculate_priority(
                        avg_speedup, opt["effort"]
                    ),
                )
                recommendations.append(optimization)

        # Sort by priority
        recommendations.sort(key=lambda x: x.priority, reverse=True)

        return recommendations

    async def generate_optimized_pipeline(
        self,
        original_config: PipelineConfig,
        optimizations: List[str]
    ) -> str:
        """
        Генерация оптимизированного pipeline

        Args:
            original_config: Оригинальная конфигурация
            optimizations: Список применяемых оптимизаций

        Returns:
            Оптимизированная YAML конфигурация
        """
        try:
            # This is a simplified example
            # Real implementation would parse and modify YAML
            optimized = {
                "name": f"Optimized {original_config.name}",
                "on": ["push", "pull_request"],
                "jobs": {
                    "build": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "name": "Checkout",
                                "uses": "actions/checkout@v4"
                            },
                            {
                                "name": "Setup Cache",
                                "uses": "actions/cache@v3",
                                "with": {
                                    "path": "~/.cache",
                                    "key": "${{ runner.os }}-build-"
                                           "${{ hashFiles('**/package-lock.json') }}",
                                },
                            },
                            {
                                "name": "Build",
                                "run": "npm ci && npm run build"
                            },
                        ],
                    },
                    "test": {
                        "runs-on": "ubuntu-latest",
                        "strategy": {"matrix": {"node": ["16", "18", "20"]}},
                        "steps": [
                            {
                                "name": "Checkout",
                                "uses": "actions/checkout@v4"
                            },
                            {
                                "name": "Test",
                                "run": "npm test -- --parallel"
                            },
                        ],
                    },
                },
            }

            return yaml.dump(
                optimized,
                default_flow_style=False,
                allow_unicode=True
            )

        except Exception as e:
            logger.error("Failed to generate optimized pipeline: %s", e)
            raise PipelineOptimizationError(
                f"Failed to generate optimized pipeline: {e}",
                details={"original_config": original_config.name}
            )

    def _calculate_health_score(self, metrics: PipelineMetrics) -> float:
        """
        Расчет health score (0-10)

        Args:
            metrics: Метрики pipeline

        Returns:
            Health score от 0 до 10
        """
        total = metrics.total_duration

        # Thresholds
        if total < 600:  # < 10 min
            return 9.5
        elif total < 900:  # < 15 min
            return 8.0
        elif total < 1200:  # < 20 min
            return 6.5
        elif total < 1800:  # < 30 min
            return 5.0
        else:
            return 3.0

    def _calculate_priority(self, speedup: float, effort: str) -> int:
        """
        Расчет приоритета оптимизации

        Args:
            speedup: Ожидаемое ускорение (0.0-1.0)
            effort: Уровень усилий (low/medium/high)

        Returns:
            Приоритет от 0 до 10
        """
        # Higher speedup + lower effort = higher priority
        effort_weights = {"low": 1.5, "medium": 1.0, "high": 0.5}
        return int(speedup * 10 * effort_weights.get(effort, 1.0))


__all__ = ["PipelineOptimizer"]
