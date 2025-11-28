"""Server Configuration Analyzer Service."""

from typing import List

from ..domain import ConfigAnalysis, ConfigIssue, ConfigSeverity, ServerConfig


class ServerConfigAnalyzer:
    """Service for analyzing 1C server configuration."""

    def __init__(self):
        """Initialize analyzer with recommended values."""
        self.recommended_memory_mb = 4096
        self.recommended_connections = 100
        self.recommended_threads = 8
        self.recommended_cache_mb = 1024

    def analyze_config(self, config: ServerConfig) -> ConfigAnalysis:
        """
        Analyze server configuration.

        Args:
            config: Server configuration

        Returns:
            Configuration analysis with issues and recommendations
        """
        issues = []
        recommendations = []

        # Check memory settings
        if config.max_memory_mb < self.recommended_memory_mb:
            issues.append(
                ConfigIssue(
                    parameter="max_memory_mb",
                    current_value=config.max_memory_mb,
                    recommended_value=self.recommended_memory_mb,
                    severity=ConfigSeverity.HIGH,
                    description=f"Memory is below recommended {self.recommended_memory_mb}MB",
                    impact="May cause out-of-memory errors under load",
                )
            )
            recommendations.append(
                f"Increase max_memory_mb to {self.recommended_memory_mb}MB"
            )

        # Check connection pool
        if config.max_connections < self.recommended_connections:
            issues.append(
                ConfigIssue(
                    parameter="max_connections",
                    current_value=config.max_connections,
                    recommended_value=self.recommended_connections,
                    severity=ConfigSeverity.MEDIUM,
                    description="Connection pool size is low",
                    impact="May reject connections under high load",
                )
            )
            recommendations.append(
                f"Increase max_connections to {self.recommended_connections}"
            )

        # Check thread pool
        if config.thread_pool_size < self.recommended_threads:
            issues.append(
                ConfigIssue(
                    parameter="thread_pool_size",
                    current_value=config.thread_pool_size,
                    recommended_value=self.recommended_threads,
                    severity=ConfigSeverity.MEDIUM,
                    description="Thread pool is undersized",
                    impact="May cause slow request processing",
                )
            )
            recommendations.append(
                f"Increase thread_pool_size to {self.recommended_threads}"
            )

        # Check cache size
        if config.cache_size_mb < self.recommended_cache_mb:
            issues.append(
                ConfigIssue(
                    parameter="cache_size_mb",
                    current_value=config.cache_size_mb,
                    recommended_value=self.recommended_cache_mb,
                    severity=ConfigSeverity.LOW,
                    description="Cache size is small",
                    impact="May increase database load",
                )
            )
            recommendations.append(
                f"Increase cache_size_mb to {self.recommended_cache_mb}MB"
            )

        # Check debug mode in production
        if config.debug_mode:
            issues.append(
                ConfigIssue(
                    parameter="debug_mode",
                    current_value=True,
                    recommended_value=False,
                    severity=ConfigSeverity.CRITICAL,
                    description="Debug mode enabled in production",
                    impact="Security risk and performance degradation",
                )
            )
            recommendations.append("Disable debug_mode in production")

        # Calculate score
        score = self._calculate_score(issues)

        return ConfigAnalysis(
            config=config, score=score, issues=issues, recommendations=recommendations
        )

    def _calculate_score(self, issues: List[ConfigIssue]) -> float:
        """Calculate configuration score (0-100)."""
        if not issues:
            return 100.0

        # Deduct points based on severity
        score = 100.0
        severity_weights = {
            ConfigSeverity.CRITICAL: 30,
            ConfigSeverity.HIGH: 20,
            ConfigSeverity.MEDIUM: 10,
            ConfigSeverity.LOW: 5,
            ConfigSeverity.INFO: 2,
        }

        for issue in issues:
            score -= severity_weights.get(issue.severity, 5)

        return max(0.0, score)

    def generate_optimized_config(self, config: ServerConfig) -> ServerConfig:
        """
        Generate optimized configuration.

        Args:
            config: Current configuration

        Returns:
            Optimized configuration
        """
        return ServerConfig(
            server_name=config.server_name,
            port=config.port,
            cluster_port=config.cluster_port,
            max_memory_mb=max(config.max_memory_mb, self.recommended_memory_mb),
            max_connections=max(config.max_connections, self.recommended_connections),
            thread_pool_size=max(config.thread_pool_size, self.recommended_threads),
            cache_size_mb=max(config.cache_size_mb, self.recommended_cache_mb),
            temp_dir=config.temp_dir,
            debug_mode=False,  # Always disable in production
            log_level=config.log_level,
        )
