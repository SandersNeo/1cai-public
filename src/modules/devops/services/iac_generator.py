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

    async def generate_terraform(self, requirements: Dict[str, Any]) -> Dict[str, str]:
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
            main_tf = self._generate_main_tf(provider, services, env)
            variables_tf = self._generate_variables_tf()
            outputs_tf = self._generate_outputs_tf(services)

            return {
                "main.tf": main_tf,
                "variables.tf": variables_tf,
                "outputs.tf": outputs_tf,
            }
        except Exception as e:
            logger.error("Terraform generation failed: %s", e)
            raise IaCGenerationError(
                f"Failed to generate Terraform: {e}",
                details={"provider": provider}
            )

    async def generate_ansible(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        Генерация Ansible playbook

        Args:
            requirements: {
                "tasks": ["install_nginx", "setup_postgres"],
                "target_os": "ubuntu",
                "environment": "production"
            }

        Returns:
            Ansible файлы (playbook.yml, inventory.ini)
        """
        tasks = requirements.get("tasks", [])
        target_os = requirements.get("target_os", "ubuntu")
        env = requirements.get("environment", "production")

        logger.info(
            "Generating Ansible playbook",
            extra={"tasks": tasks, "environment": env}
        )

        try:
            playbook = self._generate_ansible_playbook(tasks, target_os, env)
            inventory = self._generate_ansible_inventory(env)

            return {
                "playbook.yml": playbook,
                "inventory.ini": inventory,
            }
        except Exception as e:
            logger.error("Ansible generation failed: %s", e)
            raise IaCGenerationError(
                f"Failed to generate Ansible: {e}",
                details={"tasks": tasks}
            )

    async def generate_kubernetes(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """
        Генерация Kubernetes manifests

        Args:
            requirements: {
                "app_name": "my-app",
                "replicas": 3,
                "image": "my-app:1.0.0",
                "port": 8080
            }

        Returns:
            Kubernetes файлы (deployment.yaml, service.yaml)
        """
        app_name = requirements.get("app_name", "app")
        replicas = requirements.get("replicas", 3)
        image = requirements.get("image", "nginx:latest")
        port = requirements.get("port", 80)

        logger.info(
            "Generating Kubernetes manifests",
            extra={"app": app_name, "replicas": replicas}
        )

        try:
            deployment = self._generate_k8s_deployment(app_name, replicas, image, port)
            service = self._generate_k8s_service(app_name, port)
            ingress = self._generate_k8s_ingress(app_name)

            return {
                "deployment.yaml": deployment,
                "service.yaml": service,
                "ingress.yaml": ingress,
            }
        except Exception as e:
            logger.error("Kubernetes generation failed: %s", e)
            raise IaCGenerationError(
                f"Failed to generate Kubernetes: {e}",
                details={"app_name": app_name}
            )

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

    def _generate_ansible_playbook(
        self, tasks: List[str], target_os: str, env: str
    ) -> str:
        """Генерация Ansible playbook"""
        playbook = f"""---
# Ansible Playbook for {env} environment
# Target OS: {target_os}

- name: Configure servers
  hosts: all
  become: yes

  vars:
    environment: {env}

  tasks:
"""

        if "install_nginx" in tasks:
            playbook += """
    - name: Install Nginx
      apt:
        name: nginx
        state: present
        update_cache: yes
      when: ansible_os_family == "Debian"

    - name: Start Nginx
      service:
        name: nginx
        state: started
        enabled: yes

"""

        if "setup_postgres" in tasks:
            playbook += """
    - name: Install PostgreSQL
      apt:
        name: postgresql
        state: present
      when: ansible_os_family == "Debian"

    - name: Start PostgreSQL
      service:
        name: postgresql
        state: started
        enabled: yes

"""

        return playbook

    def _generate_ansible_inventory(self, env: str) -> str:
        """Генерация Ansible inventory"""
        return f"""# Ansible Inventory for {env}

[webservers]
web1.{env}.example.com
web2.{env}.example.com

[databases]
db1.{env}.example.com

[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/id_rsa
"""

    def _generate_k8s_deployment(
        self, app_name: str, replicas: int, image: str, port: int
    ) -> str:
        """Генерация Kubernetes Deployment"""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {image}
        ports:
        - containerPort: {port}
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: {port}
          initialDelaySeconds: 5
          periodSeconds: 5
"""

    def _generate_k8s_service(self, app_name: str, port: int) -> str:
        """Генерация Kubernetes Service"""
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {app_name}
spec:
  selector:
    app: {app_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: {port}
  type: LoadBalancer
"""

    def _generate_k8s_ingress(self, app_name: str) -> str:
        """Генерация Kubernetes Ingress"""
        return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: {app_name}.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {app_name}
            port:
              number: 80
"""


__all__ = ["IaCGenerator"]
