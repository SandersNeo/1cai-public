import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from src.modules.scenario_hub.domain.models import Scenario, ScenarioExecution, ScenarioStatus, StepStatus
from src.modules.scenario_hub.domain.exceptions import ScenarioNotFound, ExecutionError
from src.modules.scenario_hub.services.step_executor import StepExecutor
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ScenarioEngine:
    """Core engine for executing scenarios."""

    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        self.executions: Dict[str, ScenarioExecution] = {}
        self.step_executor = StepExecutor()

    def register_scenario(self, scenario: Scenario) -> Scenario:
        """Registers a new scenario."""
        self.scenarios[scenario.id] = scenario
        logger.info(f"Registered scenario: {scenario.id}")
        return scenario

    def get_scenario(self, scenario_id: str) -> Scenario:
        """Retrieves a scenario by ID."""
        if scenario_id not in self.scenarios:
            raise ScenarioNotFound(f"Scenario {scenario_id} not found")
        return self.scenarios[scenario_id]

    async def execute_scenario(self, scenario_id: str, parameters: Dict[str, Any] = None) -> ScenarioExecution:
        """
        Executes a scenario.

        Args:
            scenario_id: ID of the scenario to execute.
            parameters: Runtime parameters (overrides defaults).

        Returns:
            ScenarioExecution: The execution record.
        """
        scenario = self.get_scenario(scenario_id)

        # Merge parameters
        final_parameters = {**scenario.default_parameters, **(parameters or {})}

        # Create execution record
        execution = ScenarioExecution(
            id=str(uuid.uuid4()),
            scenario_id=scenario.id,
            status=ScenarioStatus.RUNNING,
            start_time=datetime.utcnow(),
            parameters=final_parameters,
        )
        self.executions[execution.id] = execution

        try:
            logger.info(f"Starting execution {execution.id} for scenario {scenario.id}")

            # Context for execution (starts with parameters)
            context = execution.parameters.copy()

            for step in scenario.steps:
                # Execute step
                step_result = await self.step_executor.execute(step, context)
                execution.step_executions.append(step_result)

                # Update context with result if available
                if step_result.status == StepStatus.COMPLETED and isinstance(step_result.result, dict):
                    context.update(step_result.result)

                if step_result.status == StepStatus.FAILED:
                    raise ExecutionError(f"Step {step.id} failed: {step_result.error}")

            execution.status = ScenarioStatus.COMPLETED
            execution.result = {"steps_completed": len(execution.step_executions)}

        except Exception as e:
            logger.error(f"Execution {execution.id} failed: {e}")
            execution.status = ScenarioStatus.FAILED
            execution.error = str(e)
        finally:
            execution.end_time = datetime.utcnow()

        return execution

    def get_execution(self, execution_id: str) -> ScenarioExecution:
        """Retrieves an execution record."""
        if execution_id not in self.executions:
            raise ExecutionError(f"Execution {execution_id} not found")
        return self.executions[execution_id]
