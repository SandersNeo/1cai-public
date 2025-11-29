# [NEXUS IDENTITY] ID: 6575367605745973363 | DATE: 2025-11-27

"""
Enhanced DevOps AI Agent
"""

import logging
from typing import Any, Dict, List, Optional

from src.ai.agents.base_agent import AgentCapability, BaseAgent
from src.ai.llm import TaskType

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
                AgentCapability.DEVOPS,
                AgentCapability.LOG_ANALYSIS,
            ]
        )
        self.logger = logging.getLogger("devops_agent_enhanced")

        # Initialize new services
        from src.modules.devops.services import (
            CostOptimizer,
            DockerAnalyzer,
            IaCGenerator,
            LogAnalyzer,
            PipelineOptimizer,
        )
        self.pipeline_optimizer = PipelineOptimizer()
        self.log_analyzer = LogAnalyzer()
        self.cost_optimizer = CostOptimizer()
        self.iac_generator = IaCGenerator()
        self.docker_analyzer = DockerAnalyzer()

        # Legacy stubs (for backward compatibility)
        self.k8s_client = None
        self.ci_client = None

        self.logger.info("DevOps Agent Enhanced initialized with modular services")

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
            analysis = await self.llm_selector.generate(
                task_type=TaskType.LOG_ANALYSIS,
                prompt=f"""
                Проанализируй логи {source}:

                {sanitized_logs}

                Найди:
                1. Ошибки и warnings
                2. Performance bottlenecks
                3. Security issues
                4. Рекомендации по оптимизации

                Формат: JSON
                """,
                context={"source": source}
            )

            return {
                "analysis": analysis["response"],
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Log analysis failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def optimize_cicd(
        self,
        pipeline_config: str
    ) -> Dict[str, Any]:
        """
        Оптимизация CI/CD pipeline

        Args:
            pipeline_config: Конфигурация pipeline

        Returns:
            Рекомендации по оптимизации
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        try:
            optimization = await self.llm_selector.generate(
                task_type=TaskType.METRICS_ANALYSIS,
                prompt=f"""
                Оптимизируй CI/CD pipeline:

                Конфигурация: {pipeline_config}

                Предложи:
                1. Параллелизацию задач
                2. Кэширование зависимостей
                3. Оптимизацию Docker образов
                4. Сокращение времени сборки

                Формат: JSON с recommendations
                """,
                context={"platform": "GitLab CI"}
            )

            return {
                "recommendations": optimization["response"],
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("CI/CD optimization failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def deploy_kubernetes(
        self,
        app_name: str,
        image: str,
        replicas: int = 3
    ) -> Dict[str, Any]:
        """
        Деплой в Kubernetes

        Args:
            app_name: Название приложения
            image: Docker образ
            replicas: Количество реплик

        Returns:
            Результат деплоя
        """
        if not self.k8s_client:
            return {
                "status": "k8s_not_configured",
                "recommendation": "Configure Kubernetes client"
            }

        # TODO: Integrate with Kubernetes API
        return {
            "app_name": app_name,
            "status": "pending_implementation"
        }

    async def detect_log_anomalies(
        self,
        logs: List[Dict[str, Any]],
        train_first: bool = False
    ) -> Dict[str, Any]:
        """
        ML-based anomaly detection in logs

        Args:
            logs: List of log entries with metadata
            train_first: Whether to train model first

        Returns:
            Detected anomalies
        """
        try:
            # Train if requested
            if train_first:
                train_result = self.anomaly_detector.train(logs, "logs")
                if train_result["status"] != "trained":
                    return train_result

            # Detect anomalies
            detection = self.anomaly_detector.detect(logs, "logs")

            # Enhance with LLM analysis if anomalies found
            if self.llm_selector and detection.get("anomalies"):
                anomalies_summary = "\n".join([
                    f"- {a['data'].get('message', 'N/A')[:100]}..."
                    for a in detection["anomalies"][:5]
                ])

                llm_analysis = await self.llm_selector.generate(
                    task_type=TaskType.LOG_ANALYSIS,
                    prompt=f"""
                    ML обнаружил аномалии в логах:

                    Аномалии:
                    {anomalies_summary}

                    Проанализируй:
                    1. Возможные причины
                    2. Критичность
                    3. Рекомендации по исправлению

                    Формат: JSON
                    """,
                    context={"task": "anomaly_analysis"}
                )

                detection["llm_analysis"] = llm_analysis.get("response", "")

            return detection

        except Exception as e:
            self.logger.error("Anomaly detection failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def detect_metric_anomalies(
        self,
        metrics: List[Dict[str, Any]],
        train_first: bool = False
    ) -> Dict[str, Any]:
        """
        ML-based anomaly detection in metrics

        Args:
            metrics: List of metric data points
            train_first: Whether to train model first

        Returns:
            Detected anomalies
        """
        try:
            # Train if requested
            if train_first:
                train_result = self.anomaly_detector.train(metrics, "metrics")
                if train_result["status"] != "trained":
                    return train_result

            # Detect anomalies
            detection = self.anomaly_detector.detect(metrics, "metrics")

            # Enhance with LLM if anomalies found
            if self.llm_selector and detection.get("anomalies"):
                anomalies_info = []
                for a in detection["anomalies"][:5]:
                    data = a["data"]
                    anomalies_info.append(
                        f"CPU: {data.get('cpu_usage', 0)}%, "
                        f"Memory: {data.get('memory_usage', 0)}%, "
                        f"Errors: {data.get('error_rate', 0)}"
                    )

                llm_analysis = await self.llm_selector.generate(
                    task_type=TaskType.METRICS_ANALYSIS,
                    prompt=f"""
                    ML обнаружил аномалии в метриках:

                    {chr(10).join(anomalies_info)}

                    Определи:
                    1. Тип проблемы (CPU/Memory/Network)
                    2. Срочность
                    3. Действия для mitigation

                    Формат: JSON
                    """,
                    context={"task": "metric_anomaly_analysis"}
                )

                detection["llm_analysis"] = llm_analysis.get("response", "")

            return detection

        except Exception as e:
            self.logger.error("Metric anomaly detection failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def auto_scale(
        self,
        app_name: str,
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Auto-scaling на основе метрик

        Args:
            app_name: Название приложения
            metrics: Метрики (CPU, memory, RPS)

        Returns:
            Решение по scaling
        """
        if not self.llm_selector:
            return {"status": "llm_not_available"}

        try:
            decision = await self.llm_selector.generate(
                task_type=TaskType.SCALING_DECISION,
                prompt=f"""
                Реши нужен ли scaling для приложения:

                App: {app_name}
                CPU: {metrics.get('cpu', 0)}%
                Memory: {metrics.get('memory', 0)}%
                RPS: {metrics.get('rps', 0)}

                Верни: action (scale_up/scale_down/no_action), replicas, reasoning
                """,
                context={"platform": "kubernetes"}
            )

            return {
                "decision": decision["response"],
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Auto-scaling decision failed: %s", e)
            return {"status": "failed", "error": str(e)}

    # ==================== NEW METHODS: Modular Services Integration ====================

    async def optimize_pipeline(
        self,
        pipeline_config: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        CI/CD Pipeline optimization using PipelineOptimizer service

        Args:
            pipeline_config: Pipeline configuration (name, platform, config_yaml)
            metrics: Optional metrics (total_duration, build_time, test_time, etc.)

        Returns:
            Analysis and optimization recommendations
        """
        try:
            # Convert dict to Pydantic models
            config = PipelineConfig(**pipeline_config)
            metrics_obj = PipelineMetrics(**metrics) if metrics else None

            # Use service
            analysis = await self.pipeline_optimizer.analyze_pipeline(
                config, metrics_obj
            )
            recommendations = await self.pipeline_optimizer.recommend_optimizations(
                config, metrics_obj or PipelineMetrics(total_duration=1500)
            )

            # Convert Pydantic to dict
            return {
                "analysis": analysis,
                "recommendations": [r.model_dump() for r in recommendations],
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Pipeline optimization failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def analyze_logs_enhanced(
        self,
        log_file: str,
        log_type: str = "application"
    ) -> Dict[str, Any]:
        """
        Enhanced log analysis using LogAnalyzer service + LLM

        Args:
            log_file: Path to log file or log content
            log_type: Type of logs (application, system, security, audit)

        Returns:
            Comprehensive log analysis with ML + LLM insights
        """
        try:
            # Use service for pattern matching and anomaly detection
            result = await self.log_analyzer.analyze_logs(log_file, log_type)

            # Enhance with LLM if available and errors found
            if self.llm_selector and result.summary.get("errors_found", 0) > 0:
                errors_summary = "\n".join([
                    f"- {cat}: {count}"
                    for cat, count in result.errors_by_category.items()
                ])

                llm_analysis = await self.llm_selector.generate(
                    task_type=TaskType.LOG_ANALYSIS,
                    prompt=f"""
                    Проанализированы логи {log_type}:

                    Найдено ошибок: {result.summary['errors_found']}
                    По категориям:
                    {errors_summary}

                    Аномалии: {len(result.anomalies)}

                    Предложи:
                    1. Root cause analysis
                    2. Priority actions
                    3. Prevention strategies

                    Формат: JSON
                    """,
                    context={"log_type": log_type}
                )

                return {
                    "service_analysis": result.model_dump(),
                    "llm_insights": llm_analysis.get("response", ""),
                    "status": "completed"
                }

            return {
                "service_analysis": result.model_dump(),
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Enhanced log analysis failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def optimize_infrastructure_costs(
        self,
        current_setup: Dict[str, Any],
        usage_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Infrastructure cost optimization using CostOptimizer service

        Args:
            current_setup: Current infrastructure config
                          (provider, instance_type, instance_count, pricing_model)
            usage_metrics: Resource usage metrics (cpu_avg, memory_avg, etc.)

        Returns:
            Cost optimization recommendations with savings
        """
        try:
            # Convert to Pydantic models
            setup = InfrastructureConfig(**current_setup)
            metrics = UsageMetrics(**usage_metrics)

            # Use service
            result = await self.cost_optimizer.analyze_costs(setup, metrics)

            return {
                "optimization_result": result.model_dump(),
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Cost optimization failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def generate_infrastructure_code(
        self,
        iac_type: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Infrastructure as Code using IaCGenerator service

        Args:
            iac_type: Type of IaC (terraform, ansible, kubernetes)
            requirements: Requirements dict (provider, services, environment, etc.)

        Returns:
            Generated IaC files
        """
        try:
            if iac_type == "terraform":
                files = await self.iac_generator.generate_terraform(requirements)
            elif iac_type == "ansible":
                files = await self.iac_generator.generate_ansible(requirements)
            elif iac_type == "kubernetes":
                files = await self.iac_generator.generate_kubernetes(requirements)
            else:
                return {
                    "status": "failed",
                    "error": f"Unsupported IaC type: {iac_type}"
                }

            return {
                "iac_type": iac_type,
                "files": files,
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("IaC generation failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def analyze_docker_infrastructure(
        self,
        compose_file_path: str = "docker-compose.yml"
    ) -> Dict[str, Any]:
        """
        Analyze Docker infrastructure using DockerAnalyzer service

        Args:
            compose_file_path: Path to docker-compose.yml

        Returns:
            Comprehensive Docker infrastructure analysis
        """
        try:
            # Use service
            result = await self.docker_analyzer.analyze_infrastructure(
                compose_file_path
            )

            return {
                "infrastructure_analysis": result,
                "status": "completed"
            }
        except Exception as e:
            self.logger.error("Docker infrastructure analysis failed: %s", e)
            return {"status": "failed", "error": str(e)}


__all__ = ["DevOpsAgentEnhanced"]
