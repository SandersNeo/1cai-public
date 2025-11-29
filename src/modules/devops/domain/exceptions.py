"""
DevOps Domain Exceptions

Domain-specific исключения для DevOps модуля.
"""
from typing import Any, Dict


class DevOpsAgentError(Exception):
    """Базовое исключение для DevOps Agent"""

    def __init__(self, message: str, details: Dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class PipelineOptimizationError(DevOpsAgentError):
    """Ошибка при оптимизации CI/CD pipeline"""


class LogAnalysisError(DevOpsAgentError):
    """Ошибка при анализе логов"""


class CostOptimizationError(DevOpsAgentError):
    """Ошибка при оптимизации затрат"""


class IaCGenerationError(DevOpsAgentError):
    """Ошибка при генерации Infrastructure as Code"""


class DockerAnalysisError(DevOpsAgentError):
    """Ошибка при анализе Docker инфраструктуры"""


__all__ = [
    "DevOpsAgentError",
    "PipelineOptimizationError",
    "LogAnalysisError",
    "CostOptimizationError",
    "IaCGenerationError",
    "DockerAnalysisError",
]
