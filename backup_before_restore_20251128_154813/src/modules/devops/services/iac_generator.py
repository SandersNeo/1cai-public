"""
IaC Generator Service

Сервис для генерации Infrastructure as Code (Terraform, Ansible, Kubernetes).
Перенесено и рефакторено из devops_agent_extended.py.
"""

from typing import Any, Dict, List

from src.modules.devops.domain.exceptions import IaCGenerationError
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class IaCGenerator:
    """
    Сервис генерации Infrastructure as Code

    Features:
    - Генерация Terraform конфигураций (AWS, Azure, GCP)
    - Генерация Ansible playbooks
    - Генерация Kubernetes manifests
    """

    async def generate_terraform(
            self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        Генерация Terraform кода

        Args:
            requirements: {
                "provider": "aws",  # aws, azure, gcp
                "services": ["compute", "database", "cache"],
                "environment": "production"
            }

        Returns:
            Terraform файлы (main.tf, variables.tf, outputs.tf)
        """
        provider = requirements.get("provider", "aws")
        services = requirements.get("services", [])
        env = requirements.get("environment", "production")

        logger.info(
            "Generating Terraform configuration",
            extra={"provider": provider, "environment": env}
        )

        try:
