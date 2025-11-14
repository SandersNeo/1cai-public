"""
DevOps AI Agent Extended
AI ассистент для DevOps инженеров с полным функционалом
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import yaml
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class CICDPipelineOptimizer:
    """Оптимизатор CI/CD pipeline"""
    
    def __init__(self):
        self.optimizations_db = self._load_optimizations_db()
    
    def _load_optimizations_db(self) -> List[Dict]:
        """База знаний оптимизаций"""
        return [
            {
                "name": "Docker Layer Caching",
                "stage": "build",
                "description": "Use Docker layer caching to speed up builds",
                "implementation": "Add cache-from and cache-to flags",
                "speedup_range": [0.3, 0.6],
                "effort": "low"
            },
            {
                "name": "Parallel Test Execution",
                "stage": "test",
                "description": "Run tests in parallel across multiple workers",
                "implementation": "Use pytest-xdist or similar",
                "speedup_range": [0.4, 0.8],
                "effort": "medium"
            },
            {
                "name": "Dependency Caching",
                "stage": "build",
                "description": "Cache npm/pip/maven dependencies",
                "implementation": "Use actions/cache or setup-* actions",
                "speedup_range": [0.2, 0.5],
                "effort": "low"
            },
            {
                "name": "Incremental Builds",
                "stage": "build",
                "description": "Build only changed modules",
                "implementation": "Use build tools with incremental support",
                "speedup_range": [0.5, 0.9],
                "effort": "high"
            },
            {
                "name": "Matrix Strategy",
                "stage": "test",
                "description": "Run tests for multiple versions in parallel",
                "implementation": "GitHub Actions matrix strategy",
                "speedup_range": [0.3, 0.7],
                "effort": "low"
            },
            {
                "name": "Conditional Job Execution",
                "stage": "all",
                "description": "Skip jobs when not needed (e.g., docs-only changes)",
                "implementation": "path filters and conditionals",
                "speedup_range": [0.1, 0.3],
                "effort": "low"
            }
        ]
    
    async def analyze_pipeline(
        self,
        pipeline_config: Dict,
        metrics: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Анализ CI/CD pipeline
        
        Args:
            pipeline_config: YAML конфигурация pipeline (GitHub Actions, GitLab CI)
            metrics: Метрики выполнения (build time, test time, etc.)
        
        Returns:
            Детальный анализ с рекомендациями
        """
        logger.info("Analyzing CI/CD pipeline")
        
        # Parse metrics
        if metrics is None:
            metrics = {
                "total_duration": 1500,  # 25 min
                "build_time": 300,       # 5 min
                "test_time": 900,        # 15 min
                "deploy_time": 300       # 5 min
            }
        
        # Analyze stages
        stages_analysis = {}
        
        # Build stage
        if metrics.get("build_time", 0) > 180:  # > 3 min
            stages_analysis["build"] = {
                "status": "needs_optimization",
                "current_time": metrics["build_time"],
                "issues": [
                    "Build time exceeds 3 minutes",
                    "Possible lack of caching",
                    "Docker layers not optimized"
                ]
            }
        
        # Test stage
        if metrics.get("test_time", 0) > 600:  # > 10 min
            stages_analysis["test"] = {
                "status": "needs_optimization",
                "current_time": metrics["test_time"],
                "issues": [
                    "Test time exceeds 10 minutes",
                    "Tests not running in parallel",
                    "Possible slow integration tests"
                ]
            }
        
        # Deploy stage
        if metrics.get("deploy_time", 0) > 240:  # > 4 min
            stages_analysis["deploy"] = {
                "status": "needs_optimization",
                "current_time": metrics["deploy_time"],
                "issues": [
                    "Deploy time exceeds 4 minutes",
                    "Possible inefficient deployment strategy"
                ]
            }
        
        return {
            "current_metrics": metrics,
            "stages_analysis": stages_analysis,
            "overall_health": self._calculate_health_score(metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    async def recommend_optimizations(
        self,
        pipeline_config: Dict,
        metrics: Dict
    ) -> List[Dict[str, Any]]:
        """
        Рекомендации по оптимизации
        
        Returns:
            Список рекомендаций с ожидаемым эффектом
        """
        recommendations = []
        
        # Analyze current pipeline
        analysis = await self.analyze_pipeline(pipeline_config, metrics)
        
        # Match optimizations to problems
        for opt in self.optimizations_db:
            stage = opt["stage"]
            
            # Check if this stage needs optimization
            if stage == "all" or stage in analysis["stages_analysis"]:
                speedup_min, speedup_max = opt["speedup_range"]
                avg_speedup = (speedup_min + speedup_max) / 2
                
                recommendations.append({
                    "optimization": opt["name"],
                    "stage": stage,
                    "description": opt["description"],
                    "implementation": opt["implementation"],
                    "expected_speedup_percent": int(avg_speedup * 100),
                    "effort": opt["effort"],
                    "priority": self._calculate_priority(avg_speedup, opt["effort"])
                })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        
        return recommendations
    
    async def generate_optimized_pipeline(
        self,
        original_config: Dict,
        optimizations: List[str]
    ) -> str:
        """
        Генерация оптимизированного pipeline
        
        Args:
            original_config: Оригинальная конфигурация
            optimizations: Список применяемых оптимизаций
        
        Returns:
            Оптимизированная YAML конфигурация
        """
        # This is a simplified example
        # Real implementation would parse and modify YAML
        
        optimized = {
            "name": "Optimized CI/CD Pipeline",
            "on": ["push", "pull_request"],
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"name": "Checkout", "uses": "actions/checkout@v4"},
                        {
                            "name": "Setup Cache",
                            "uses": "actions/cache@v3",
                            "with": {
                                "path": "~/.cache",
                                "key": "${{ runner.os }}-build-${{ hashFiles('**/package-lock.json') }}"
                            }
                        },
                        {"name": "Build", "run": "npm ci && npm run build"}
                    ]
                },
                "test": {
                    "runs-on": "ubuntu-latest",
                    "strategy": {
                        "matrix": {
                            "node": ["16", "18", "20"]
                        }
                    },
                    "steps": [
                        {"name": "Checkout", "uses": "actions/checkout@v4"},
                        {"name": "Test", "run": "npm test -- --parallel"}
                    ]
                }
            }
        }
        
        return yaml.dump(optimized, default_flow_style=False, allow_unicode=True)
    
    def _calculate_health_score(self, metrics: Dict) -> float:
        """Расчет health score (0-10)"""
        total = metrics.get("total_duration", 0)
        
        # Thresholds
        if total < 600:  # < 10 min
            return 9.5
        elif total < 900:  # < 15 min
            return 8.0
        elif total < 1200:  # < 20 min
            return 6.5
        elif total < 1800:  # < 30 min
            return 5.0
        else:
            return 3.0
    
    def _calculate_priority(self, speedup: float, effort: str) -> int:
        """Расчет приоритета оптимизации"""
        # Higher speedup + lower effort = higher priority
        effort_weights = {"low": 1.5, "medium": 1.0, "high": 0.5}
        return int(speedup * 10 * effort_weights.get(effort, 1.0))


class LogAnalyzer:
    """AI анализатор логов"""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.anomaly_threshold = 3.0  # Standard deviations
    
    def _load_error_patterns(self) -> List[Dict]:
        """База паттернов ошибок"""
        return [
            {
                "pattern": r"OutOfMemoryError|MemoryError",
                "category": "memory",
                "severity": "critical",
                "diagnosis": "Memory exhaustion"
            },
            {
                "pattern": r"Connection refused|Connection timeout",
                "category": "network",
                "severity": "high",
                "diagnosis": "Network connectivity issues"
            },
            {
                "pattern": r"Deadlock|Lock wait timeout",
                "category": "database",
                "severity": "critical",
                "diagnosis": "Database lock contention"
            },
            {
                "pattern": r"Permission denied|Access denied",
                "category": "security",
                "severity": "high",
                "diagnosis": "Permission or access control issue"
            },
            {
                "pattern": r"Null pointer|NullPointerException",
                "category": "code",
                "severity": "medium",
                "diagnosis": "Null reference error"
            }
        ]
    
    async def analyze_logs(
        self,
        log_file: str,
        log_type: str = "application"
    ) -> Dict[str, Any]:
        """
        AI анализ логов
        
        Args:
            log_file: Путь к файлу логов или текст логов
            log_type: Тип логов (application, system, security, audit)
        
        Returns:
            Детальный анализ с аномалиями и рекомендациями
        """
        logger.info(
            "Analyzing logs",
            extra={"log_type": log_type}
        )
        
        # Read logs
        if Path(log_file).exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        else:
            log_content = log_file  # Assume it's the log content itself
        
        # Parse logs
        errors = []
        warnings = []
        anomalies = []
        
        # Pattern matching
        for line in log_content.split('\n'):
            # Check error patterns
            for pattern_info in self.error_patterns:
                if re.search(pattern_info["pattern"], line, re.IGNORECASE):
                    errors.append({
                        "line": line,
                        "category": pattern_info["category"],
                        "severity": pattern_info["severity"],
                        "diagnosis": pattern_info["diagnosis"]
                    })
            
            # Check for warnings
            if re.search(r"WARN|WARNING", line, re.IGNORECASE):
                warnings.append(line)
        
        # Detect anomalies (simplified)
        # In real implementation, would use time-series analysis
        error_rate = len(errors) / max(len(log_content.split('\n')), 1)
        if error_rate > 0.1:  # > 10% error rate
            anomalies.append({
                "type": "High error rate",
                "timestamp": datetime.now().isoformat(),
                "severity": "high",
                "metric": f"Error rate: {error_rate:.2%}",
                "possible_cause": "System degradation or service outage"
            })
        
        # Pattern analysis
        patterns = self._detect_patterns(errors)
        
        # Recommendations
        recommendations = self._generate_recommendations(errors, anomalies)
        
        return {
            "summary": {
                "errors_found": len(errors),
                "warnings_found": len(warnings),
                "anomalies_found": len(anomalies),
                "log_type": log_type
            },
            "errors_by_category": self._group_by_category(errors),
            "anomalies": anomalies,
            "patterns": patterns,
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }
    
    def _group_by_category(self, errors: List[Dict]) -> Dict[str, int]:
        """Группировка ошибок по категориям"""
        categories = {}
        for error in errors:
            cat = error.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        return categories
    
    def _detect_patterns(self, errors: List[Dict]) -> List[Dict]:
        """Детекция паттернов в ошибках"""
        patterns = []
        
        # Group by category
        by_category = self._group_by_category(errors)
        
        for category, count in by_category.items():
            if count > 10:
                patterns.append({
                    "pattern": f"High frequency of {category} errors",
                    "count": count,
                    "significance": "high" if count > 50 else "medium"
                })
        
        return patterns
    
    def _generate_recommendations(
        self,
        errors: List[Dict],
        anomalies: List[Dict]
    ) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []
        
        # Based on errors
        by_category = self._group_by_category(errors)
        
        if by_category.get("memory", 0) > 5:
            recommendations.append(
                "Investigate memory usage - possible memory leak or insufficient heap size"
            )
        
        if by_category.get("database", 0) > 10:
            recommendations.append(
                "Review database configuration - high number of database errors detected"
            )
        
        if by_category.get("network", 0) > 5:
            recommendations.append(
                "Check network connectivity and firewall rules"
            )
        
        # Based on anomalies
        if len(anomalies) > 0:
            recommendations.append(
                "Set up alerting for error rate > 5%"
            )
        
        return recommendations


class CostOptimizer:
    """Оптимизатор затрат на инфраструктуру"""
    
    def __init__(self):
        self.rightsizing_rules = self._load_rightsizing_rules()
    
    def _load_rightsizing_rules(self) -> List[Dict]:
        """Правила rightsizing"""
        return [
            {
                "condition": "cpu_usage < 20",
                "action": "downsize",
                "savings_percent": 0.5
            },
            {
                "condition": "cpu_usage < 40",
                "action": "downsize_one_tier",
                "savings_percent": 0.3
            },
            {
                "condition": "memory_usage < 30",
                "action": "memory_optimized_instance",
                "savings_percent": 0.25
            },
            {
                "condition": "storage_iops < 1000",
                "action": "use_standard_storage",
                "savings_percent": 0.4
            }
        ]
    
    async def analyze_costs(
        self,
        current_setup: Dict,
        usage_metrics: Dict
    ) -> Dict[str, Any]:
        """
        Анализ затрат на инфраструктуру
        
        Args:
            current_setup: Текущая инфраструктура
            usage_metrics: Метрики использования
        
        Returns:
            Анализ с рекомендациями
        """
        logger.info("Analyzing infrastructure costs")
        
        # Calculate current cost (simplified)
        current_cost = self._calculate_cost(current_setup)
        
        # Find optimization opportunities
        optimizations = []
        
        # CPU-based
        cpu_usage = usage_metrics.get("cpu_avg", 50)
        if cpu_usage < 40:
            optimizations.append({
                "resource": "Compute instances",
                "current": current_setup.get("instance_type", "m5.2xlarge"),
                "recommended": self._downsize_instance(current_setup.get("instance_type")),
                "current_cost": current_cost * 0.6,
                "optimized_cost": current_cost * 0.4,
                "savings_month": current_cost * 0.2,
                "savings_percent": 33,
                "reason": f"Low CPU utilization ({cpu_usage}%)",
                "risk": "low",
                "effort": "low"
            })
        
        # Memory-based
        memory_usage = usage_metrics.get("memory_avg", 60)
        if memory_usage < 50:
            optimizations.append({
                "resource": "Memory allocation",
                "current": "64 GB",
                "recommended": "32 GB",
                "current_cost": current_cost * 0.3,
                "optimized_cost": current_cost * 0.15,
                "savings_month": current_cost * 0.15,
                "savings_percent": 50,
                "reason": f"Low memory utilization ({memory_usage}%)",
                "risk": "medium",
                "effort": "medium"
            })
        
        # Reserved instances
        if current_setup.get("pricing_model") == "on_demand":
            optimizations.append({
                "resource": "Pricing model",
                "current": "On-Demand",
                "recommended": "Reserved Instances (1-year)",
                "current_cost": current_cost,
                "optimized_cost": current_cost * 0.6,
                "savings_month": current_cost * 0.4,
                "savings_percent": 40,
                "reason": "Predictable workload suitable for Reserved Instances",
                "risk": "low",
                "effort": "low"
            })
        
        # Calculate total optimized cost
        total_savings = sum(opt["savings_month"] for opt in optimizations)
        optimized_cost = current_cost - total_savings
        
        return {
            "current_cost_month": current_cost,
            "optimized_cost_month": optimized_cost,
            "total_savings_month": total_savings,
            "savings_percent": int((total_savings / current_cost) * 100) if current_cost > 0 else 0,
            "optimizations": optimizations,
            "annual_savings": total_savings * 12,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_cost(self, setup: Dict) -> float:
        """Расчет стоимости (упрощенный)"""
        # Mock pricing
        instance_prices = {
            "m5.large": 100,
            "m5.xlarge": 200,
            "m5.2xlarge": 400,
            "m5.4xlarge": 800,
            "db.m5.large": 150,
            "db.m5.xlarge": 300,
            "db.m5.2xlarge": 600
        }
        
        instance_type = setup.get("instance_type", "m5.2xlarge")
        count = setup.get("instance_count", 3)
        
        return instance_prices.get(instance_type, 400) * count
    
    def _downsize_instance(self, current: str) -> str:
        """Даунсайз инстанса"""
        mapping = {
            "m5.4xlarge": "m5.2xlarge",
            "m5.2xlarge": "m5.xlarge",
            "m5.xlarge": "m5.large",
            "db.m5.2xlarge": "db.m5.xlarge",
            "db.m5.xlarge": "db.m5.large"
        }
        return mapping.get(current, current)


class IaCGenerator:
    """Генератор Infrastructure as Code"""
    
    async def generate_terraform(
        self,
        requirements: Dict
    ) -> Dict[str, str]:
        """
        Генерация Terraform кода
        
        Args:
            requirements: {
                "provider": "aws",
                "services": ["compute", "database", "cache"],
                "environment": "production"
            }
        
        Returns:
            Terraform файлы (main.tf, variables.tf, outputs.tf)
        """
        provider = requirements.get("provider", "aws")
        services = requirements.get("services", [])
        env = requirements.get("environment", "production")
        
        main_tf = self._generate_main_tf(provider, services, env)
        variables_tf = self._generate_variables_tf()
        outputs_tf = self._generate_outputs_tf(services)
        
        return {
            "main.tf": main_tf,
            "variables.tf": variables_tf,
            "outputs.tf": outputs_tf
        }
    
    def _generate_main_tf(self, provider: str, services: List[str], env: str) -> str:
        """Генерация main.tf"""
        tf = f"""# Terraform configuration for {env} environment
# Provider: {provider}

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}

"""
        
        # Add compute if requested
        if "compute" in services:
            tf += """
# EC2 Instances
resource "aws_instance" "app_server" {
  count         = var.instance_count
  ami           = var.ami_id
  instance_type = var.instance_type
  
  tags = {
    Name        = "${{var.project_name}}-app-${{count.index}}"
    Environment = var.environment
  }
}

"""
        
        # Add database if requested
        if "database" in services:
            tf += """
# RDS Database
resource "aws_db_instance" "main" {
  identifier           = "${{var.project_name}}-db"
  engine              = "postgres"
  engine_version      = "15.3"
  instance_class      = var.db_instance_class
  allocated_storage   = var.db_storage_gb
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  skip_final_snapshot = false
  final_snapshot_identifier = "${{var.project_name}}-final-snapshot"
  
  tags = {
    Name        = "${{var.project_name}}-database"
    Environment = var.environment
  }
}

"""
        
        # Add cache if requested
        if "cache" in services:
            tf += """
# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${{var.project_name}}-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  
  tags = {
    Name        = "${{var.project_name}}-cache"
    Environment = var.environment
  }
}

"""
        
        return tf
    
    def _generate_variables_tf(self) -> str:
        """Генерация variables.tf"""
        return """# Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 2
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "ami_id" {
  description = "AMI ID for EC2 instances"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_storage_gb" {
  description = "RDS storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
"""
    
    def _generate_outputs_tf(self, services: List[str]) -> str:
        """Генерация outputs.tf"""
        outputs = "# Outputs\n\n"
        
        if "compute" in services:
            outputs += """
output "instance_ids" {
  description = "IDs of EC2 instances"
  value       = aws_instance.app_server[*].id
}

output "instance_public_ips" {
  description = "Public IPs of EC2 instances"
  value       = aws_instance.app_server[*].public_ip
}

"""
        
        if "database" in services:
            outputs += """
output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
}

"""
        
        return outputs


class DevOpsAgentExtended:
    """
    Расширенный DevOps AI ассистент
    
    Возможности:
    - CI/CD Pipeline оптимизация
    - AI анализ логов
    - Cost optimization
    - IaC генерация (Terraform, Ansible)
    """
    
    def __init__(self):
        self.cicd_optimizer = CICDPipelineOptimizer()
        self.log_analyzer = LogAnalyzer()
        self.cost_optimizer = CostOptimizer()
        self.iac_generator = IaCGenerator()
        
        logger.info("DevOps Agent Extended initialized")
    
    async def optimize_pipeline(
        self,
        pipeline_config: Dict,
        metrics: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Полная оптимизация CI/CD pipeline
        
        Returns:
            {
                "analysis": {...},
                "recommendations": [...],
                "optimized_pipeline": "...",
                "expected_improvement": {...}
            }
        """
        # Analyze
        analysis = await self.cicd_optimizer.analyze_pipeline(pipeline_config, metrics)
        
        # Get recommendations
        recommendations = await self.cicd_optimizer.recommend_optimizations(
            pipeline_config,
            metrics or {}
        )
        
        # Generate optimized pipeline
        opt_names = [rec["optimization"] for rec in recommendations[:3]]
        optimized_pipeline = await self.cicd_optimizer.generate_optimized_pipeline(
            pipeline_config,
            opt_names
        )
        
        # Calculate expected improvement
        total_speedup = sum(rec["expected_speedup_percent"] for rec in recommendations[:3]) / 100
        current_time = (metrics or {}).get("total_duration", 1500)
        expected_time = int(current_time * (1 - min(total_speedup, 0.7)))
        
        return {
            "analysis": analysis,
            "recommendations": recommendations,
            "optimized_pipeline": optimized_pipeline,
            "expected_improvement": {
                "current_duration_sec": current_time,
                "expected_duration_sec": expected_time,
                "time_saved_sec": current_time - expected_time,
                "speedup_percent": int((1 - expected_time / current_time) * 100)
            }
        }
    
    async def analyze_logs(
        self,
        log_source: str,
        log_type: str = "application"
    ) -> Dict[str, Any]:
        """AI анализ логов"""
        return await self.log_analyzer.analyze_logs(log_source, log_type)
    
    async def optimize_costs(
        self,
        infrastructure: Dict,
        metrics: Dict
    ) -> Dict[str, Any]:
        """Оптимизация затрат"""
        return await self.cost_optimizer.analyze_costs(infrastructure, metrics)
    
    async def generate_iac(
        self,
        requirements: Dict
    ) -> Dict[str, str]:
        """Генерация IaC (Terraform)"""
        return await self.iac_generator.generate_terraform(requirements)


