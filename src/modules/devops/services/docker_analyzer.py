"""
Docker Analyzer Service

Сервис для анализа Docker инфраструктуры согласно Clean Architecture.
Перенесено и рефакторено из devops_agent_extended.py.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import yaml

from src.modules.devops.domain.exceptions import DockerAnalysisError
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class DockerAnalyzer:
    """
    Сервис анализа Docker инфраструктуры

    Features:
    - Анализ docker-compose.yml на best practices
    - Проверка runtime статуса контейнеров
    - Security и performance recommendations
    """

    def __init__(self):
        """Инициализация Docker Analyzer"""

    async def analyze_compose_file(self, file_path: str) -> Dict[str, Any]:
        """
        Анализ docker-compose.yml на предмет best practices и проблем

        Args:
            file_path: Путь к docker-compose.yml

        Returns:
            Детальный анализ с рекомендациями
        """
        logger.info("Analyzing docker-compose file: %s", file_path)

        try:
            # Read and parse compose file
            compose_path = Path(file_path)
            if not compose_path.exists():
                raise DockerAnalysisError(
                    f"Compose file not found: {file_path}",
                    details={"file_path": file_path}
                )

            with open(compose_path, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            services = compose_data.get("services", {})
            analysis = {
                "service_count": len(services),
                "version": compose_data.get("version", "unknown"),
                "services_analysis": {},
                "security_issues": [],
                "performance_issues": [],
                "recommendations": [],
            }

            # Analyze each service
            for name, config in services.items():
                service_analysis = self._analyze_service(name, config)
                analysis["services_analysis"][name] = service_analysis

                # Collect issues
                analysis["security_issues"].extend(service_analysis["security_issues"])
                analysis["performance_issues"].extend(
                    service_analysis["performance_issues"]
                )

            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis)

            return analysis

        except yaml.YAMLError as e:
            logger.error("Failed to parse YAML: %s", e)
            raise DockerAnalysisError(
                f"Invalid YAML format: {e}",
                details={"file_path": file_path}
            )
        except Exception as e:
            logger.error(f"Failed to analyze compose file: {e}", exc_info=True)
            raise DockerAnalysisError(
                f"Analysis failed: {e}",
                details={"file_path": file_path}
            )

    async def check_runtime_status(self) -> List[Dict[str, Any]]:
        """
        Проверка реально запущенных контейнеров через docker CLI

        Returns:
            Список запущенных контейнеров с их статусами
        """
        logger.info("Checking Docker runtime status")

        try:
            # Use docker ps with JSON formatting
            cmd = ["docker", "ps", "--format", "{{json .}}"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=10
            )

            if result.returncode != 0:
                logger.warning(f"docker ps failed: {result.stderr}")
                return []

            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        c_data = json.loads(line)
                        containers.append(
                            {
                                "id": c_data.get("ID"),
                                "name": c_data.get("Names"),
                                "image": c_data.get("Image"),
                                "status": c_data.get("Status"),
                                "state": c_data.get("State", "running"),
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            logger.info(f"Found {len(containers)} running containers")
            return containers

        except FileNotFoundError:
            logger.error("Docker CLI not found")
            return []
        except subprocess.TimeoutExpired:
            logger.error("Docker command timed out")
            return []
        except Exception as e:
            logger.error(f"Failed to check runtime status: {e}", exc_info=True)
            return []

    async def analyze_infrastructure(
        self, compose_file_path: str = "docker-compose.yml"
    ) -> Dict[str, Any]:
        """
        Полный анализ Docker инфраструктуры (Static + Runtime)

        Args:
            compose_file_path: Путь к docker-compose.yml

        Returns:
            Комплексный анализ инфраструктуры
        """
        logger.info("Analyzing Docker infrastructure")

        try:
            # 1. Static Analysis
            static_analysis = await self.analyze_compose_file(compose_file_path)

            # 2. Runtime Analysis
            runtime_containers = await self.check_runtime_status()

            # 3. Correlation (find containers matching services)
            services_status = {}
            if "services_analysis" in static_analysis:
                for svc_name in static_analysis["services_analysis"].keys():
                    # Simple heuristic: find service name in container name
                    found = next(
                        (c for c in runtime_containers if svc_name in c["name"]), None
                    )
                    services_status[svc_name] = {
                        "runtime_status": found["status"] if found else "not_running",
                        "container_id": found["id"] if found else None,
                        "is_running": found is not None,
                    }

            return {
                "static_analysis": static_analysis,
                "runtime_containers": runtime_containers,
                "services_status": services_status,
                "summary": {
                    "total_services": static_analysis.get("service_count", 0),
                    "running_containers": len(runtime_containers),
                    "security_issues_count": len(
                        static_analysis.get("security_issues", [])
                    ),
                    "performance_issues_count": len(
                        static_analysis.get("performance_issues", [])
                    ),
                },
            }

        except Exception as e:
            logger.error("Infrastructure analysis failed: %s", e)
            raise DockerAnalysisError(
                f"Failed to analyze infrastructure: {e}",
                details={"compose_file": compose_file_path}
            )

    def _analyze_service(self, name: str, config: Dict) -> Dict[str, Any]:
        """Анализ отдельного сервиса"""
        service_issues = []
        security_issues = []
        performance_issues = []

        # 1. Check Image Versions (avoid 'latest')
        image = config.get("image", "")
        if ":latest" in image or (":" not in image and image):
            issue = {
                "severity": "medium",
                "message": f"Service '{name}' uses 'latest' tag in image '{image}'",
                "recommendation": "Pin specific image version for reproducibility",
            }
            service_issues.append(issue["message"])
            security_issues.append(issue)

        # 2. Check Restart Policy
        restart = config.get("restart", "")
        if not restart:
            issue = {
                "severity": "low",
                "message": f"Service '{name}' has no restart policy",
                "recommendation": "Add restart: unless-stopped or restart: always",
            }
            service_issues.append(issue["message"])
            performance_issues.append(issue)

        # 3. Check Healthchecks
        critical_services = ["postgres", "redis", "neo4j", "mysql", "mongodb"]
        if "healthcheck" not in config and name in critical_services:
            issue = {
                "severity": "high",
                "message": f"Critical service '{name}' missing healthcheck",
                "recommendation": "Add healthcheck configuration for better reliability",
            }
            service_issues.append(issue["message"])
            performance_issues.append(issue)

        # 4. Check Resource Limits
        deploy = config.get("deploy", {})
        resources = deploy.get("resources", {})
        if not resources and name in critical_services:
            issue = {
                "severity": "medium",
                "message": f"Service '{name}' has no resource limits",
                "recommendation": "Add memory and CPU limits to prevent resource exhaustion",
            }
            service_issues.append(issue["message"])
            performance_issues.append(issue)

        # 5. Check for privileged mode (security risk)
        if config.get("privileged", False):
            issue = {
                "severity": "critical",
                "message": f"Service '{name}' runs in privileged mode",
                "recommendation": "Avoid privileged mode unless absolutely necessary",
            }
            service_issues.append(issue["message"])
            security_issues.append(issue)

        return {
            "image": image,
            "issues": service_issues,
            "security_issues": security_issues,
            "performance_issues": performance_issues,
            "status": "ok" if not service_issues else "attention_needed",
        }

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Генерация общих рекомендаций"""
        recommendations = []

        # Security recommendations
        security_count = len(analysis.get("security_issues", []))
        if security_count > 0:
            recommendations.append(
                f"Fix {security_count} security issue(s) - pin image versions and avoid privileged mode"
            )

        # Performance recommendations
        perf_count = len(analysis.get("performance_issues", []))
        if perf_count > 0:
            recommendations.append(
                f"Address {perf_count} performance issue(s) - add healthchecks and resource limits"
            )

        # General best practices
        if analysis.get("version") == "unknown":
            recommendations.append(
                "Specify compose file version (e.g., version: '3.8')")

        return recommendations


__all__ = ["DockerAnalyzer"]
