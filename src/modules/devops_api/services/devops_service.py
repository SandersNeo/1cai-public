from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from src.utils.structured_logging import StructuredLogger

if TYPE_CHECKING:
    from src.ai.agents.devops_agent_extended import DevOpsAgentExtended
    from src.ai.self_evolving_ai import SelfEvolvingAI

logger = StructuredLogger(__name__).logger


class DevOpsService:
    """Service for DevOps operations."""

    def __init__(self):
        self._agent: Optional["DevOpsAgentExtended"] = None

    @property
    def agent(self) -> "DevOpsAgentExtended":
        if self._agent is None:
            from src.ai.agents.devops_agent_extended import DevOpsAgentExtended
            self._agent = DevOpsAgentExtended()
        return self._agent

    async def analyze_infrastructure(self, compose_file: Optional[str] = None) -> Dict[str, Any]:
        """Analyze Docker infrastructure."""
        if not compose_file:
            project_root = Path.cwd()
            possible_paths = [
                project_root / "docker-compose.yml",
                project_root / "docker-compose.mvp.yml",
                project_root / "docker-compose.yaml",
            ]

            for path in possible_paths:
                if path.exists():
                    compose_file = str(path)
                    break

            if not compose_file:
                raise FileNotFoundError(
                    "docker-compose.yml not found. Please specify compose_file parameter.")

        if not Path(compose_file).exists():
            raise FileNotFoundError(f"File not found: {compose_file}")

        result = await self.agent.analyze_local_infrastructure(compose_file_path=compose_file)

        logger.info(
            "Infrastructure analysis completed",
            extra={
                "compose_file": compose_file,
                "services_count": result.get("service_count", 0),
                "issues_count": len(result.get("security_issues", [])) + len(result.get("performance_issues", [])),
            },
        )

        return result

    async def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get quick infrastructure status."""
        containers = await self.agent.docker_analyzer.check_runtime_status()
        return {"status": "success", "containers": containers, "count": len(containers)}


class AIEvolutionService:
    """Service for Self-Evolving AI operations."""

    def __init__(self):
        self._ai: Optional["SelfEvolvingAI"] = None

    @property
    def ai(self) -> "SelfEvolvingAI":
        if self._ai is None:
            from src.ai.self_evolving_ai import SelfEvolvingAI
            self._ai = SelfEvolvingAI(llm_provider=None)
        return self._ai

    async def evolve(self, force: bool = False) -> Dict[str, Any]:
        """Run AI evolution cycle."""
        if self.ai._is_evolving:
            return {
                "status": "in_progress",
                "stage": self.ai._evolution_stage.value,
                "message": "Evolution already in progress",
            }

        if self.ai.llm_provider is None:
            metrics = await self.ai._analyze_performance()
            return {
                "status": "partial",
                "stage": "analyzing",
                "metrics": {
                    "accuracy": metrics.accuracy,
                    "error_rate": metrics.error_rate,
                    "latency_ms": metrics.latency_ms,
                    "throughput": metrics.throughput,
                    "user_satisfaction": metrics.user_satisfaction,
                },
                "improvements": [],
                "message": "LLM provider not configured. Only performance analysis available.",
            }

        result = await self.ai.evolve()

        logger.info(
            "AI evolution completed",
            extra={
                "status": result.get("status"),
                "improvements_count": len(result.get("improvements", [])),
            },
        )

        return result

    async def get_status(self) -> Dict[str, Any]:
        """Get evolution status."""
        latest_metrics = None
        if self.ai._performance_history:
            latest = self.ai._performance_history[-1]
            latest_metrics = {
                "accuracy": latest.accuracy,
                "error_rate": latest.error_rate,
                "latency_ms": latest.latency_ms,
                "throughput": latest.throughput,
                "user_satisfaction": latest.user_satisfaction,
            }

        return {
            "is_evolving": self.ai._is_evolving,
            "current_stage": self.ai._evolution_stage.value,
            "performance_history_count": len(self.ai._performance_history),
            "improvements_count": len(self.ai._improvements),
            "latest_metrics": latest_metrics,
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics history."""
        metrics_history = []
        for metrics in self.ai._performance_history:
            metrics_history.append(
                {
                    "accuracy": metrics.accuracy,
                    "error_rate": metrics.error_rate,
                    "latency_ms": metrics.latency_ms,
                    "throughput": metrics.throughput,
                    "user_satisfaction": metrics.user_satisfaction,
                }
            )

        return {"count": len(metrics_history), "history": metrics_history}
