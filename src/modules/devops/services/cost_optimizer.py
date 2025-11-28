"""
Cost Optimizer Service

Сервис для оптимизации затрат на инфраструктуру согласно Clean Architecture.
Перенесено и рефакторено из devops_agent_extended.py.
"""

from typing import Dict, List

from src.modules.devops.domain.exceptions import CostOptimizationError
from src.modules.devops.domain.models import (
    CostOptimization,
    CostOptimizationResult,
    InfrastructureConfig,
    OptimizationEffort,
    UsageMetrics,
)
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CostOptimizer:
    """
    Сервис оптимизации затрат на инфраструктуру

    Features:
    - Анализ текущих затрат
    - Rightsizing рекомендации
    - Reserved instances оптимизация
    - Расчет потенциальной экономии
    """

    def __init__(self, rightsizing_repository=None):
        """
        Args:
            rightsizing_repository: Repository для правил rightsizing
                                   (опционально, для dependency injection)
        """
        self.rightsizing_repository = rightsizing_repository
        self.rightsizing_rules = self._load_rightsizing_rules()

    def _load_rightsizing_rules(self) -> List[Dict]:
        """
        Правила rightsizing

        TODO: Перенести в OptimizationRepository
        """
        return [
            {
                "condition": "cpu_usage < 20",
                "action": "downsize",
                "savings_percent": 0.5,
            },
            {
                "condition": "cpu_usage < 40",
                "action": "downsize_one_tier",
                "savings_percent": 0.3,
            },
            {
                "condition": "memory_usage < 30",
                "action": "memory_optimized_instance",
                "savings_percent": 0.25,
            },
            {
                "condition": "storage_iops < 1000",
                "action": "use_standard_storage",
                "savings_percent": 0.4,
            },
        ]

    async def analyze_costs(
        self,
        current_setup: InfrastructureConfig,
        usage_metrics: UsageMetrics
    ) -> CostOptimizationResult:
        """
        Анализ затрат на инфраструктуру

        Args:
            current_setup: Текущая конфигурация инфраструктуры
            usage_metrics: Метрики использования ресурсов

        Returns:
            Результат анализа с рекомендациями по оптимизации
        """
        logger.info(
            "Analyzing infrastructure costs",
            extra={"provider": current_setup.provider}
        )

        try:
            # Calculate current cost
            current_cost = self._calculate_cost(current_setup)

            # Find optimization opportunities
            optimizations = []

            # CPU-based optimization
            if usage_metrics.cpu_avg < 40:
                cpu_opt = self._create_cpu_optimization(
                    current_setup, usage_metrics, current_cost
                )
                optimizations.append(cpu_opt)

            # Memory-based optimization
            if usage_metrics.memory_avg < 50:
                memory_opt = self._create_memory_optimization(
                    current_setup, usage_metrics, current_cost
                )
                optimizations.append(memory_opt)

            # Reserved instances optimization
            if current_setup.pricing_model == "on_demand":
                reserved_opt = self._create_reserved_instances_optimization(
                    current_setup, current_cost
                )
                optimizations.append(reserved_opt)

            # Calculate totals
            total_savings = sum(opt.savings_month for opt in optimizations)
            optimized_cost = current_cost - total_savings
            savings_percent = (
                int((total_savings / current_cost) * 100) if current_cost > 0 else 0
            )

            return CostOptimizationResult(
                current_cost_month=current_cost,
                optimized_cost_month=optimized_cost,
                total_savings_month=total_savings,
                savings_percent=savings_percent,
                optimizations=optimizations,
                annual_savings=total_savings * 12,
            )

        except Exception as e:
            logger.error("Cost analysis failed: %s", e)
            raise CostOptimizationError(
                f"Failed to analyze costs: {e}",
                details={"provider": current_setup.provider}
            )

    def _create_cpu_optimization(
        self,
        setup: InfrastructureConfig,
        metrics: UsageMetrics,
        current_cost: float
    ) -> CostOptimization:
        """Создание рекомендации по оптимизации CPU"""
        return CostOptimization(
            resource="Compute instances",
            current=setup.instance_type,
            recommended=self._downsize_instance(setup.instance_type),
            current_cost=current_cost * 0.6,
            optimized_cost=current_cost * 0.4,
            savings_month=current_cost * 0.2,
            savings_percent=33,
            reason=f"Low CPU utilization ({metrics.cpu_avg:.1f}%)",
            risk="low",
            effort=OptimizationEffort.LOW,
        )

    def _create_memory_optimization(
        self,
        setup: InfrastructureConfig,
        metrics: UsageMetrics,
        current_cost: float
    ) -> CostOptimization:
        """Создание рекомендации по оптимизации памяти"""
        return CostOptimization(
            resource="Memory allocation",
            current="64 GB",
            recommended="32 GB",
            current_cost=current_cost * 0.3,
            optimized_cost=current_cost * 0.15,
            savings_month=current_cost * 0.15,
            savings_percent=50,
            reason=f"Low memory utilization ({metrics.memory_avg:.1f}%)",
            risk="medium",
            effort=OptimizationEffort.MEDIUM,
        )

    def _create_reserved_instances_optimization(
        self,
        setup: InfrastructureConfig,
        current_cost: float
    ) -> CostOptimization:
        """Создание рекомендации по Reserved Instances"""
        return CostOptimization(
            resource="Pricing model",
            current="On-Demand",
            recommended="Reserved Instances (1-year)",
            current_cost=current_cost,
            optimized_cost=current_cost * 0.6,
            savings_month=current_cost * 0.4,
            savings_percent=40,
            reason="Predictable workload suitable for Reserved Instances",
            risk="low",
            effort=OptimizationEffort.LOW,
        )

    def _calculate_cost(self, setup: InfrastructureConfig) -> float:
        """
        Расчет стоимости инфраструктуры

        Args:
            setup: Конфигурация инфраструктуры

        Returns:
            Месячная стоимость в USD
        """
        # Mock pricing (в реальной реализации использовать API cloud provider)
        instance_prices = {
            "m5.large": 100,
            "m5.xlarge": 200,
            "m5.2xlarge": 400,
            "m5.4xlarge": 800,
            "db.m5.large": 150,
            "db.m5.xlarge": 300,
            "db.m5.2xlarge": 600,
            # Azure
            "Standard_D2s_v3": 150,
            "Standard_D4s_v3": 300,
            # GCP
            "n1-standard-2": 120,
            "n1-standard-4": 240,
        }

        base_price = instance_prices.get(setup.instance_type, 400)
        return base_price * setup.instance_count

    def _downsize_instance(self, current: str) -> str:
        """
        Даунсайз инстанса на один tier

        Args:
            current: Текущий тип инстанса

        Returns:
            Рекомендуемый тип инстанса
        """
        # AWS mapping
        aws_mapping = {
            "m5.4xlarge": "m5.2xlarge",
            "m5.2xlarge": "m5.xlarge",
            "m5.xlarge": "m5.large",
            "db.m5.2xlarge": "db.m5.xlarge",
            "db.m5.xlarge": "db.m5.large",
        }

        # Azure mapping
        azure_mapping = {
            "Standard_D8s_v3": "Standard_D4s_v3",
            "Standard_D4s_v3": "Standard_D2s_v3",
        }

        # GCP mapping
        gcp_mapping = {
            "n1-standard-8": "n1-standard-4",
            "n1-standard-4": "n1-standard-2",
        }

        # Try all mappings
        for mapping in [aws_mapping, azure_mapping, gcp_mapping]:
            if current in mapping:
                return mapping[current]

        return current


__all__ = ["CostOptimizer"]
