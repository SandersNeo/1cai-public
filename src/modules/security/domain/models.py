"""
Security Domain Models

Pydantic модели для Security модуля согласно Clean Architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class VulnerabilityType(str, Enum):
    """Тип уязвимости"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    XXE = "xxe"
    SSRF = "ssrf"
    CODE_INJECTION = "code_injection"
    INSECURE_PROTOCOL = "insecure_protocol"
    DESERIALIZATION = "deserialization"


class Severity(str, Enum):
    """Серьезность уязвимости"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(str, Enum):
    """Уровень риска"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SecretType(str, Enum):
    """Тип секрета"""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    AWS_KEY = "aws_key"
    DATABASE_URL = "database_url"


class ComplianceFramework(str, Enum):
    """Фреймворк compliance"""
    OWASP = "owasp"
    CWE = "cwe"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"


class Vulnerability(BaseModel):
    """Уязвимость в коде"""
    type: VulnerabilityType = Field(..., description="Тип уязвимости")
    severity: Severity = Field(..., description="Серьезность")
    location: str = Field(..., description="Местоположение в коде")
    line_number: Optional[int] = Field(None, description="Номер строки")
    description: str = Field(..., description="Описание уязвимости")
    recommendation: str = Field(..., description="Рекомендация по исправлению")
    cwe_id: Optional[str] = Field(None, description="CWE ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "sql_injection",
                "severity": "critical",
                "location": "user_service.py",
                "line_number": 42,
                "description": "SQL injection vulnerability detected",
                "recommendation": "Use parameterized queries",
                "cwe_id": "CWE-89"
            }
        }
    )


class VulnerabilityScanResult(BaseModel):
    """Результат сканирования уязвимостей"""
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list,
        description="Обнаруженные уязвимости"
    )
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Оценка риска (0-100)"
    )
    severity_breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Распределение по серьезности"
    )
    scan_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp сканирования"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vulnerabilities": [],
                "risk_score": 45.5,
                "severity_breakdown": {
                    "critical": 1,
                    "high": 2,
                    "medium": 3,
                    "low": 5
                },
                "scan_timestamp": "2025-11-27T10:00:00"
            }
        }
    )


class DependencyVulnerability(BaseModel):
    """Уязвимость в зависимости"""
    package_name: str = Field(..., description="Название пакета")
    version: str = Field(..., description="Версия пакета")
    cve_id: str = Field(..., description="CVE ID")
    severity: Severity = Field(..., description="Серьезность")
    description: str = Field(..., description="Описание уязвимости")
    fixed_version: Optional[str] = Field(
        None,
        description="Версия с исправлением"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "package_name": "requests",
                "version": "2.25.0",
                "cve_id": "CVE-2023-12345",
                "severity": "high",
                "description": "Remote code execution vulnerability",
                "fixed_version": "2.31.0"
            }
        }
    )


class DependencyAuditResult(BaseModel):
    """Результат аудита зависимостей"""
    total_dependencies: int = Field(..., ge=0, description="Всего зависимостей")
    vulnerable_dependencies: List[DependencyVulnerability] = Field(
        default_factory=list,
        description="Уязвимые зависимости"
    )
    risk_level: RiskLevel = Field(..., description="Уровень риска")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Рекомендации"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp аудита"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_dependencies": 50,
                "vulnerable_dependencies": [],
                "risk_level": "medium",
                "recommendations": [
                    "Update requests to 2.31.0",
                    "Review django version"
                ],
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


class Secret(BaseModel):
    """Обнаруженный секрет"""
    type: SecretType = Field(..., description="Тип секрета")
    value_preview: str = Field(..., description="Превью значения (замаскировано)")
    location: str = Field(..., description="Местоположение")
    line_number: int = Field(..., ge=1, description="Номер строки")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Уверенность (0-1)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "api_key",
                "value_preview": "sk-***************",
                "location": "config.py",
                "line_number": 15,
                "confidence": 0.95
            }
        }
    )


class SecretDetectionResult(BaseModel):
    """Результат детекции секретов"""
    secrets_found: List[Secret] = Field(
        default_factory=list,
        description="Обнаруженные секреты"
    )
    total_count: int = Field(..., ge=0, description="Всего найдено")
    high_confidence_count: int = Field(
        ...,
        ge=0,
        description="С высокой уверенностью (>0.8)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp детекции"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "secrets_found": [],
                "total_count": 3,
                "high_confidence_count": 2,
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


class ComplianceIssue(BaseModel):
    """Проблема compliance"""
    framework: ComplianceFramework = Field(..., description="Фреймворк")
    rule_id: str = Field(..., description="ID правила")
    description: str = Field(..., description="Описание проблемы")
    severity: Severity = Field(..., description="Серьезность")
    location: str = Field(..., description="Местоположение")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "framework": "owasp",
                "rule_id": "A01:2021",
                "description": "Broken Access Control",
                "severity": "high",
                "location": "auth_service.py"
            }
        }
    )


class ComplianceReport(BaseModel):
    """Отчет о compliance"""
    framework: ComplianceFramework = Field(..., description="Фреймворк")
    compliant: bool = Field(..., description="Соответствует ли стандарту")
    issues: List[ComplianceIssue] = Field(
        default_factory=list,
        description="Обнаруженные проблемы"
    )
    compliance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Оценка compliance (0-100)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp проверки"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "framework": "owasp",
                "compliant": False,
                "issues": [],
                "compliance_score": 75.0,
                "timestamp": "2025-11-27T10:00:00"
            }
        }
    )


__all__ = [
    "VulnerabilityType",
    "Severity",
    "RiskLevel",
    "SecretType",
    "ComplianceFramework",
    "Vulnerability",
    "VulnerabilityScanResult",
    "DependencyVulnerability",
    "DependencyAuditResult",
    "Secret",
    "SecretDetectionResult",
    "ComplianceIssue",
    "ComplianceReport",
]
