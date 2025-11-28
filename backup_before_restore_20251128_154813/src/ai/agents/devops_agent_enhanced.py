# [NEXUS IDENTITY] ID: 6575367605745973363 | DATE: 2025-11-27

"""
Enhanced DevOps AI Agent
AI ассистент для DevOps инженеров с LLM интеграцией и модульной архитектурой

Интегрирует сервисы из src/modules/devops/services согласно Clean Architecture.
"""

import logging
from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.llm import TaskType
from src.ml.anomaly_detection import get_anomaly_detector
from src.modules.devops.domain.models import (InfrastructureConfig,
                                              PipelineConfig, PipelineMetrics,
                                              UsageMetrics)
# Import DevOps services
from src.modules.devops.services import (CostOptimizer, DockerAnalyzer,
                                         IaCGenerator, LogAnalyzer,
                                         PipelineOptimizer)

logger = logging.getLogger(__name__)


class DevOpsAgentEnhanced(BaseAgent):
    """
    Enhanced AI агент для DevOps инженеров

    Features:
    - LLM-based log analysis
    - CI/CD pipeline optimization
    - Kubernetes deployment
    - Auto-scaling logic
    """

    def __init__(self):
        super().__init__(
            agent_name="devops_agent_enhanced",
            capabilities=[
                AgentCapability.DEPLOYMENT,
                AgentCapability.MONITORING,
            ]
        )
        self.logger = logging.getLogger("devops_agent_enhanced")

        # ML Anomaly Detector
        self.anomaly_detector = get_anomaly_detector()

        # Initialize DevOps services (Clean Architecture)
        self.pipeline_optimizer = PipelineOptimizer()
        self.log_analyzer = LogAnalyzer(anomaly_detector=self.anomaly_detector)
        self.cost_optimizer = CostOptimizer()
        self.iac_generator = IaCGenerator()
        self.docker_analyzer = DockerAnalyzer()

        # Legacy stubs (for backward compatibility)
        self.k8s_client = None
        self.ci_client = None

        self.logger.info(
            "DevOps Agent Enhanced initialized with modular services")

    async def analyze_logs(
        self,
        logs: List[str],
        source: str = "application"
    ) -> Dict[str, Any]:
        """
        LLM-based log analysis

        Args:
            logs: Список логов
            source: Источник логов

        Returns:
            Анализ логов
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        # Sanitize logs (remove sensitive data)
        sanitized_logs = "\n".join(logs[:100])  # Limit for LLM

        try:
