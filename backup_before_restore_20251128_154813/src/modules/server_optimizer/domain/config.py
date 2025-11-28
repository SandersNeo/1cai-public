"""Server configuration domain models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class ConfigSeverity(str, Enum):
    """Configuration issue severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ServerConfig:
    """1C Server configuration."""

    # Basic settings
    server_name: str
    port: int
    cluster_port: int

    # Performance settings
    max_memory_mb: int
    max_connections: int
    thread_pool_size: int

    # Cache settings
    cache_size_mb: int
    temp_dir: str

    # Optional settings
    debug_mode: bool = False
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate configuration."""
        if self.port < 1 or self.port > 65535:
            raise ValueError("Invalid port number")
        if self.max_memory_mb < 512:
            raise ValueError("Memory must be at least 512MB")
        if self.max_connections < 1:
            raise ValueError("Max connections must be positive")


@dataclass
class ConfigIssue:
    """Configuration issue."""

    parameter: str
    current_value: any
    recommended_value: any
    severity: ConfigSeverity
    description: str
    impact: str


@dataclass
class ConfigAnalysis:
    """Server configuration analysis result."""

    config: ServerConfig
    score: float  # 0-100
    issues: List[ConfigIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def critical_issues(self) -> List[ConfigIssue]:
        """Get critical issues."""
        return [i for i in self.issues if i.severity == ConfigSeverity.CRITICAL]

    @property
    def has_critical_issues(self) -> bool:
        """Check if has critical issues."""
        return len(self.critical_issues) > 0
