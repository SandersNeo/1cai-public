# [NEXUS IDENTITY] ID: 4109191311491825372 | DATE: 2025-11-19


class IntegrationError(RuntimeError):
    """Base error for integration failures."""


class IntegrationConfigError(IntegrationError):
    """Raised when integration configuration is missing or invalid."""
