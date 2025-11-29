import asyncio
from typing import Any, Dict
from src.modules.scenario_hub.domain.models import ScenarioStep, StepExecution, StepStatus
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class StepExecutor:
    """Выполняет отдельные шаги сценария."""

    def __init__(self):
        from src.modules.scenario_hub.services.agent_connector import AgentConnector
        from src.modules.scenario_hub.services.condition_evaluator import ConditionEvaluator

        self.agent_connector = AgentConnector()
        self.condition_evaluator = ConditionEvaluator()

    async def execute(self, step: ScenarioStep, context: Dict[str, Any] = None) -> StepExecution:
        """
        Выполняет один шаг.
        """
        execution = StepExecution(step_id=step.id, status=StepStatus.RUNNING)
        context = context or {}

        try:
            # 1. Проверка условия
            if step.condition:
                if not self.condition_evaluator.evaluate(step.condition, context):
                    logger.info(f"Пропуск шага {step.id} (Условие '{step.condition}' не выполнено)")
                    execution.status = StepStatus.SKIPPED
                    execution.result = {"skipped": True, "reason": "Условие не выполнено"}
                    return execution

            logger.info(f"Выполнение шага: {step.id} ({step.action})")

            # 2. Выполнение действия
            if step.action == "wait":
                duration = step.parameters.get("seconds", 1)
                await asyncio.sleep(duration)
                execution.result = {"waited": duration}

            elif step.action == "log":
                message = step.parameters.get("message", "")
                # Интерполяция переменных контекста
                try:
                    message = message.format(**context)
                except KeyError:
                    pass  # Игнорируем отсутствующие ключи
                logger.info(f"Лог Сценария: {message}")
                execution.logs.append(message)
                execution.result = {"logged": True}

            elif step.action == "fail":
                raise Exception("Симулированный сбой")

            elif step.action == "call_agent":
                agent = step.parameters.get("agent")
                endpoint = step.parameters.get("endpoint")
                method = step.parameters.get("method", "POST")
                data = step.parameters.get("data", {})

                # Интерполяция значений данных из контекста
                interpolated_data = {}
                for k, v in data.items():
                    if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                        key = v[1:-1]
                        if key in context:
                            interpolated_data[k] = context[key]
                        else:
                            interpolated_data[k] = v
                    else:
                        interpolated_data[k] = v

                result = await self.agent_connector.call_agent(agent, endpoint, method, interpolated_data)
                execution.result = result

            else:
                execution.result = {"action": step.action, "status": "simulated_success"}

            execution.status = StepStatus.COMPLETED

        except Exception as e:
            logger.error(f"Сбой шага: {step.id}", exc_info=True)
            execution.status = StepStatus.FAILED
            execution.error = str(e)

        return execution
