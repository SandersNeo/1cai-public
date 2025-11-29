"""
Хаб вложенных сценариев.

Самомодифицирующийся хаб автоматизации с вложенным обучением.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional

from src.ml.continual_learning.scenario_memory import ScenarioMemory
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class NestedScenarioHub:
    """Самомодифицирующийся хаб автоматизации сценариев.

    Features:
        - Многомасштабная память сценариев
        - Отслеживание паттернов успеха
        - Автоматическая оптимизация параметров
        - Самомодификация на основе обратной связи

    Example:
        >>> hub = NestedScenarioHub()
        >>> result = await hub.execute_scenario(
        ...     scenario_id="deploy_app",
        ...     parameters={"env": "staging"},
        ...     executor=deploy_function
        ... )
        >>> print(f"Success: {result['success']}")
    """

    def __init__(self, base_hub: Optional[Any] = None):
        """Инициализирует хаб вложенных сценариев.

        Args:
            base_hub: Базовый хаб сценариев (опционально).
        """
        self.base = base_hub

        # Scenario memory
        self.memory = ScenarioMemory()

        # Registered scenarios
        self.scenarios: Dict[str, Dict] = {}

        # Statistics
        self.stats = {
            "total_executions": 0,
            "total_successes": 0,
            "total_failures": 0,
            "total_modifications": 0,
            "avg_duration": 0.0,
        }

        logger.info("Created NestedScenarioHub")

    def register_scenario(
        self,
        scenario_id: str,
        executor: Callable,
        default_parameters: Optional[Dict] = None,
        description: Optional[str] = None,
    ):
        """Регистрирует сценарий.

        Args:
            scenario_id: Уникальный идентификатор сценария.
            executor: Асинхронная функция для выполнения сценария.
            default_parameters: Параметры по умолчанию.
            description: Описание сценария.
        """
        self.scenarios[scenario_id] = {
            "executor": executor,
            "default_parameters": default_parameters or {},
            "description": description or "",
            "registered_at": time.time(),
        }

        logger.info("Registered scenario: %s", scenario_id)

    async def execute_scenario(
        self,
        scenario_id: str,
        parameters: Optional[Dict] = None,
        auto_optimize: bool = True,
        executor: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Выполняет сценарий с опциональной авто-оптимизацией.

        Args:
            scenario_id: Сценарий для выполнения.
            parameters: Параметры выполнения.
            auto_optimize: Включить ли авто-оптимизацию параметров.
            executor: Опциональное переопределение исполнителя.

        Returns:
            Dict[str, Any]: Результат выполнения с метаданными.
        """
        self.stats["total_executions"] += 1
        start_time = time.time()

        # Get scenario
        if scenario_id in self.scenarios:
            scenario = self.scenarios[scenario_id]
            executor = executor or scenario["executor"]
            base_parameters = scenario["default_parameters"]
        else:
            if not executor:
                raise ValueError(f"Unknown scenario: {scenario_id}")
            base_parameters = {}

        # Merge parameters
        final_parameters = {**base_parameters, **(parameters or {})}

        # Auto-optimize if enabled
        if auto_optimize:
            optimization = self.memory.suggest_modifications(
                scenario_id, final_parameters)

            if optimization["action"] in ["replace", "modify"]:
                logger.info(
                    f"Auto-optimizing parameters for {scenario_id}",
                    extra={
                        "action": optimization["action"],
                        "reason": optimization["reason"],
                        "confidence": optimization["confidence"],
                    },
                )

                final_parameters = optimization["suggested_parameters"]
                self.stats["total_modifications"] += 1

        # Execute
        try:
            if asyncio.iscoroutinefunction(executor):
                result = await executor(**final_parameters)
            else:
                result = executor(**final_parameters)

            success = True
            error = None

        except Exception as e:
            logger.error(f"Scenario execution failed: {e}", exc_info=True, extra={
                         "scenario_id": scenario_id})
            result = None
            success = False
            error = str(e)

        # Track execution
        duration = time.time() - start_time

        self.memory.track_execution(
            scenario_id=scenario_id, success=success, duration=duration, parameters=final_parameters, error=error
        )

        # Update stats
        if success:
            self.stats["total_successes"] += 1
        else:
            self.stats["total_failures"] += 1

        self.stats["avg_duration"] = self.stats["avg_duration"] * 0.9 + duration * 0.1

        logger.info(
            "Executed scenario",
            extra={
                "scenario_id": scenario_id,
                "success": success,
                "duration": duration,
                "auto_optimized": auto_optimize,
            },
        )

        return {
            "scenario_id": scenario_id,
            "success": success,
            "result": result,
            "error": error,
            "duration": duration,
            "parameters_used": final_parameters,
            "auto_optimized": auto_optimize,
        }

    def get_scenario_analysis(self, scenario_id: str) -> Dict[str, Any]:
        """Получает анализ для сценария.

        Args:
            scenario_id: Сценарий для анализа.

        Returns:
            Dict[str, Any]: Анализ с рекомендациями.
        """
        analysis = self.memory.analyze_success_patterns(scenario_id)
        suggestions = self.memory.suggest_modifications(
            scenario_id, self.scenarios.get(
                scenario_id, {}).get("default_parameters", {})
        )

        return {**analysis, "suggestions": suggestions}

    def get_stats(self) -> Dict[str, Any]:
        """Получает статистику хаба."""
        memory_stats = self.memory.get_stats()

        success_rate = (
            self.stats["total_successes"] / self.stats["total_executions"]
            if self.stats["total_executions"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "success_rate": success_rate,
            "registered_scenarios": len(self.scenarios),
            "memory": memory_stats.to_dict(),
        }

    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья хаба."""
        memory_health = self.memory.health_check()

        return {
            "status": "healthy",
            "total_executions": self.stats["total_executions"],
            "success_rate": (
                self.stats["total_successes"] / self.stats["total_executions"]
                if self.stats["total_executions"] > 0
                else 0.0
            ),
            "registered_scenarios": len(self.scenarios),
            "memory": memory_health,
        }
